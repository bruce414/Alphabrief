"""SEC EDGAR submissions client used by the source-enrichment fallback.

EDGAR rejects requests without a User-Agent and caps anonymous traffic at
10 req/sec. This module enforces both: it always sets the configured User-Agent
and serializes outbound calls behind a per-process 100ms guard. All errors
(network, non-2xx, parse failures) are swallowed and an empty list is returned;
enrichment is best-effort and must not block the cheap pre-scan flow.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import get_settings
from app.clients.edgar_form_categories import (
    CATEGORY_VALUES,
    categorize_form,
)


logger = logging.getLogger(__name__)


# EDGAR caps anonymous traffic at 10 req/sec. 100ms keeps us comfortably under.
_MIN_INTERVAL_SECONDS = 0.1

_rate_lock = asyncio.Lock()
_last_call_ts: float = 0.0


_TICKER_CIK_CACHE: dict[str, str] = {}
_CIK_CACHE_LOCK = asyncio.Lock()
_CIK_CACHE_REFRESHED_AT: datetime | None = None
_CIK_CACHE_TTL_HOURS = 168  # 7 days


# Stable ordering for downstream prompt selection.
_CATEGORY_PRIORITY: dict[str, int] = {
    "PERIODIC": 0,
    "GOVERNANCE": 1,
    "OWNERSHIP": 2,
    "CAPITAL_RAISE": 3,
    "INSIDER": 4,
    "OTHER": 5,
}


@dataclass(frozen=True)
class EnrichmentDoc:
    """Result of an enrichment lookup. Stored as JSONB on source_scans."""

    source: str
    title: str
    url: str
    snippet: str | None
    retrieved_at: datetime
    category: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dict suitable for JSONB persistence."""

        return {
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "retrieved_at": self.retrieved_at.isoformat(),
            "category": self.category,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnrichmentDoc":
        """Best-effort decode for legacy JSONB rows (missing category → OTHER)."""

        retrieved_raw = data.get("retrieved_at")
        retrieved_at = (
            datetime.fromisoformat(retrieved_raw)
            if isinstance(retrieved_raw, str) and retrieved_raw
            else datetime.now(UTC)
        )
        category = data.get("category")
        if not isinstance(category, str) or category not in CATEGORY_VALUES:
            category = "OTHER"

        return cls(
            source=str(data.get("source") or ""),
            title=str(data.get("title") or ""),
            url=str(data.get("url") or ""),
            snippet=data.get("snippet") if isinstance(data.get("snippet"), str) else None,
            retrieved_at=retrieved_at,
            category=category,
            metadata=dict(data.get("metadata") or {}),
        )


def reset_rate_limit_state() -> None:
    """Test helper: clear the per-process 100ms throttle bookkeeping."""

    global _last_call_ts
    _last_call_ts = 0.0


def reset_cik_cache_state() -> None:
    """Test helper: clear the in-memory ticker→CIK cache."""

    global _TICKER_CIK_CACHE, _CIK_CACHE_REFRESHED_AT
    _TICKER_CIK_CACHE = {}
    _CIK_CACHE_REFRESHED_AT = None


async def _throttle() -> None:
    """Serialize outbound EDGAR calls behind a 100ms minimum interval."""

    global _last_call_ts
    async with _rate_lock:
        now = time.monotonic()
        wait = _MIN_INTERVAL_SECONDS - (now - _last_call_ts)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_ts = time.monotonic()


def _is_cik_cache_fresh() -> bool:
    if _CIK_CACHE_REFRESHED_AT is None:
        return False
    ttl = timedelta(hours=_CIK_CACHE_TTL_HOURS)
    return datetime.now(UTC) - _CIK_CACHE_REFRESHED_AT < ttl


async def _refresh_cik_cache(http_client: httpx.AsyncClient) -> None:
    """Refresh the in-memory ticker→CIK map. Best-effort, never raises."""

    global _TICKER_CIK_CACHE, _CIK_CACHE_REFRESHED_AT
    settings = get_settings()
    headers = {"User-Agent": settings.scraping_user_agent, "Accept": "application/json"}
    url = f"{settings.edgar_base_url.rstrip('/')}/files/company_tickers.json"
    try:
        await _throttle()
        response = await http_client.get(url, headers=headers)
    except (httpx.HTTPError, asyncio.TimeoutError) as exc:
        logger.warning("EDGAR ticker→CIK fetch failed: %s", exc)
        return

    if response.status_code >= 300:
        logger.warning(
            "EDGAR ticker→CIK fetch returned %s", response.status_code
        )
        return

    try:
        payload = response.json()
    except ValueError as exc:  # includes JSONDecodeError
        logger.warning("EDGAR ticker→CIK JSON decode failed: %s", exc)
        return

    if not isinstance(payload, dict):
        logger.warning("EDGAR ticker→CIK payload unexpected type")
        return

    out: dict[str, str] = {}
    for _, row in payload.items():
        if not isinstance(row, dict):
            continue
        ticker = row.get("ticker")
        cik_str = row.get("cik_str")
        if not isinstance(ticker, str) or not ticker.strip():
            continue
        if not isinstance(cik_str, int):
            continue
        out[ticker.strip().upper()] = f"{cik_str:010d}"

    if out:
        _TICKER_CIK_CACHE = out
        _CIK_CACHE_REFRESHED_AT = datetime.now(UTC)


async def _lookup_cik_for_ticker(
    ticker: str, *, http_client: httpx.AsyncClient
) -> str | None:
    """Return zero-padded 10-digit CIK for a ticker, or None."""

    async with _CIK_CACHE_LOCK:
        if not _is_cik_cache_fresh():
            await _refresh_cik_cache(http_client)
        return _TICKER_CIK_CACHE.get(ticker.upper())


async def lookup_recent_filings(
    ticker: str,
    *,
    limit_per_category: int = 3,
    categories: list[str] | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> list[EnrichmentDoc]:
    """Return recent filings for a ticker, categorized.

    If `categories` is None → return all categories except OTHER.
    Caps at `limit_per_category` per category (default 3).
    Total cap: 3 × 5 categories = 15 docs max.
    """

    if not ticker:
        return []

    settings = get_settings()
    headers = {"User-Agent": settings.scraping_user_agent, "Accept": "application/json"}

    own_client = http_client is None
    client = http_client or httpx.AsyncClient(
        timeout=httpx.Timeout(settings.fetch_timeout_seconds),
        trust_env=False,
    )
    try:
        cik = await _lookup_cik_for_ticker(ticker, http_client=client)
        if cik is None:
            return []

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            await _throttle()
            response = await client.get(url, headers=headers)
        except (httpx.HTTPError, asyncio.TimeoutError) as exc:
            logger.warning("EDGAR submissions fetch failed for %s: %s", ticker, exc)
            return []

        if response.status_code >= 300:
            logger.warning(
                "EDGAR submissions returned %s for %s", response.status_code, ticker
            )
            return []

        try:
            payload = response.json()
        except ValueError as exc:  # includes JSONDecodeError
            logger.warning("EDGAR submissions JSON decode failed for %s: %s", ticker, exc)
            return []

        return _parse_submissions_json(
            payload,
            ticker=ticker,
            cik=cik,
            limit_per_category=limit_per_category,
            categories=categories,
        )
    finally:
        if own_client:
            await client.aclose()


def _parse_submissions_json(
    payload: object,
    *,
    ticker: str,
    cik: str,
    limit_per_category: int,
    categories: list[str] | None,
) -> list[EnrichmentDoc]:
    if not isinstance(payload, dict):
        return []

    filings = payload.get("filings")
    if not isinstance(filings, dict):
        return []
    recent = filings.get("recent")
    if not isinstance(recent, dict):
        return []

    accession_numbers = recent.get("accessionNumber")
    forms = recent.get("form")
    filing_dates = recent.get("filingDate")
    primary_docs = recent.get("primaryDocument")
    if not (
        isinstance(accession_numbers, list)
        and isinstance(forms, list)
        and isinstance(filing_dates, list)
        and isinstance(primary_docs, list)
    ):
        return []

    n = len(accession_numbers)
    if not (len(forms) == len(filing_dates) == len(primary_docs) == n):
        logger.warning("EDGAR submissions arrays mismatched for %s", ticker)
        return []

    wanted: set[str]
    if categories is None:
        wanted = {c for c in CATEGORY_VALUES if c != "OTHER"}
    else:
        wanted = {c for c in categories if c in CATEGORY_VALUES}

    per_cat: dict[str, list[tuple[str, EnrichmentDoc]]] = {}
    now = datetime.now(UTC)
    cik_int = str(int(cik))  # strip left-pad zeros for archives path

    for i in range(n):
        accession = accession_numbers[i]
        form = forms[i]
        filing_date = filing_dates[i]
        primary_doc = primary_docs[i]
        if not (
            isinstance(accession, str)
            and isinstance(form, str)
            and isinstance(filing_date, str)
            and isinstance(primary_doc, str)
        ):
            continue

        category = categorize_form(form)
        if category not in wanted:
            continue

        accession_no_dashes = accession.replace("-", "")
        url = (
            "https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{accession_no_dashes}/{primary_doc}"
        )

        title = form.strip() or "EDGAR filing"
        if filing_date.strip():
            title = f"{title} — filed {filing_date.strip()}"

        meta: dict[str, Any] = {
            "ticker": ticker,
            "cik": cik,
            "form": form.strip(),
            "filed_at": filing_date.strip(),
            "accession_number": accession,
            "primary_document": primary_doc,
        }

        doc = EnrichmentDoc(
            source="EDGAR",
            title=title,
            url=url,
            snippet=None,
            retrieved_at=now,
            category=category,
            metadata=meta,
        )
        per_cat.setdefault(category, []).append((filing_date, doc))

    if limit_per_category < 1:
        limit_per_category = 1

    selected: list[EnrichmentDoc] = []
    for category, rows in per_cat.items():
        rows.sort(key=lambda pair: pair[0], reverse=True)
        selected.extend([doc for _, doc in rows[:limit_per_category]])

    # Stable two-key sort: first by filed_at desc, then by category priority asc.
    selected.sort(key=lambda d: d.metadata.get("filed_at", ""), reverse=True)
    selected.sort(key=lambda d: _CATEGORY_PRIORITY.get(d.category, 999))

    return selected
