"""SEC EDGAR atom-feed client used by the source-enrichment fallback.

EDGAR rejects requests without a User-Agent and caps anonymous traffic at
10 req/sec. This module enforces both: it always sets the configured User-Agent
and serializes outbound calls behind a per-process 100ms guard. All errors
(network, non-2xx, parse failures) are swallowed and an empty list is returned;
enrichment is best-effort and must not block the cheap pre-scan flow.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import get_settings


logger = logging.getLogger(__name__)


_ATOM_NS = "{http://www.w3.org/2005/Atom}"
# EDGAR caps anonymous traffic at 10 req/sec. 100ms keeps us comfortably under.
_MIN_INTERVAL_SECONDS = 0.1
# Match SEC accession numbers in URLs: ##########-##-######
_ACCESSION_RE = re.compile(r"(\d{10}-\d{2}-\d{6})")

_rate_lock = asyncio.Lock()
_last_call_ts: float = 0.0


@dataclass(frozen=True)
class EnrichmentDoc:
    """Result of an enrichment lookup. Stored as JSONB on source_scans."""

    source: str
    title: str
    url: str
    snippet: str | None
    retrieved_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dict suitable for JSONB persistence."""

        return {
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "retrieved_at": self.retrieved_at.isoformat(),
            "metadata": dict(self.metadata),
        }


def reset_rate_limit_state() -> None:
    """Test helper: clear the per-process 100ms throttle bookkeeping."""

    global _last_call_ts
    _last_call_ts = 0.0


async def _throttle() -> None:
    """Serialize outbound EDGAR calls behind a 100ms minimum interval."""

    global _last_call_ts
    async with _rate_lock:
        now = time.monotonic()
        wait = _MIN_INTERVAL_SECONDS - (now - _last_call_ts)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_ts = time.monotonic()


async def lookup_recent_filings(
    ticker: str,
    *,
    limit: int = 3,
    http_client: httpx.AsyncClient | None = None,
) -> list[EnrichmentDoc]:
    """Fetch the most recent EDGAR filings for ``ticker``.

    Always returns a list (possibly empty); never raises. Network errors,
    non-2xx responses, and malformed XML are swallowed.
    """

    if not ticker:
        return []

    settings = get_settings()
    url = f"{settings.edgar_base_url.rstrip('/')}/cgi-bin/browse-edgar"
    params = {
        "action": "getcompany",
        "CIK": ticker,
        "type": "",
        "dateb": "",
        "owner": "include",
        "count": str(max(int(limit), 1)),
        "output": "atom",
    }
    headers = {
        "User-Agent": settings.scraping_user_agent,
        "Accept": "application/atom+xml, application/xml;q=0.9",
    }

    own_client = http_client is None
    client = http_client or httpx.AsyncClient(
        timeout=httpx.Timeout(settings.fetch_timeout_seconds),
        trust_env=False,
    )
    try:
        await _throttle()
        try:
            response = await client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning("EDGAR fetch failed for %s: %s", ticker, exc)
            return []

        if response.status_code >= 300:
            return []

        try:
            return _parse_atom(response.text, ticker=ticker, limit=limit)
        except ET.ParseError as exc:
            logger.warning("EDGAR atom parse failed for %s: %s", ticker, exc)
            return []
    finally:
        if own_client:
            await client.aclose()


def _parse_atom(xml_text: str, *, ticker: str, limit: int) -> list[EnrichmentDoc]:
    root = ET.fromstring(xml_text)
    entries = root.findall(f"{_ATOM_NS}entry")
    out: list[EnrichmentDoc] = []
    now = datetime.now(UTC)

    for entry in entries[: max(int(limit), 1)]:
        link_el = entry.find(f"{_ATOM_NS}link[@rel='alternate']")
        if link_el is None:
            link_el = entry.find(f"{_ATOM_NS}link")
        if link_el is None or "href" not in link_el.attrib:
            continue

        title_el = entry.find(f"{_ATOM_NS}title")
        updated_el = entry.find(f"{_ATOM_NS}updated")
        summary_el = entry.find(f"{_ATOM_NS}summary")

        url = link_el.attrib["href"]
        form_type = _text(title_el)
        filing_date = _date_from_updated(_text(updated_el))

        # The atom feed sometimes hides the form code in <category term="..." />
        # when title is just "EDGAR filing"; fall back to that if needed.
        if not form_type:
            cat_el = entry.find(f"{_ATOM_NS}category")
            if cat_el is not None:
                form_type = (cat_el.attrib.get("term") or "").strip()

        title = form_type or "EDGAR filing"
        if filing_date:
            title = f"{title} — filed {filing_date}"

        meta: dict[str, Any] = {
            "ticker": ticker,
            "form": form_type or None,
            "filed_at": filing_date,
        }
        accession = _extract_accession(url)
        if accession:
            meta["accession_number"] = accession

        out.append(
            EnrichmentDoc(
                source="EDGAR",
                title=title,
                url=url,
                snippet=_text(summary_el) or None,
                retrieved_at=now,
                metadata=meta,
            )
        )
    return out


def _text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _date_from_updated(updated_text: str) -> str | None:
    """Pull the YYYY-MM-DD prefix out of an atom <updated> ISO string."""

    if not updated_text:
        return None
    return updated_text[:10] if len(updated_text) >= 10 else updated_text


def _extract_accession(url: str) -> str | None:
    match = _ACCESSION_RE.search(url)
    return match.group(1) if match else None
