"""Source-enrichment fallback for METADATA_ONLY scans (AI_PIPELINE §17.1).

When AlphaBrief cannot lawfully read a paywalled / robots-disallowed / noai
article, the cheap pre-scan still surfaces detected entities. Those entities
are used as queries against public primary-source APIs so the brief can stay
groundable without relying on the gated article body.

v0.3 first slice: SEC EDGAR ticker lookups only. Wikipedia / FRED / IR-page
adapters land in a future PR.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.clients import edgar_client
from app.clients.edgar_client import EnrichmentDoc
from app.core.config import get_settings


logger = logging.getLogger(__name__)


# Hard cap on the number of tickers we expand into EDGAR lookups per scan.
# Keeps worst-case latency bounded and avoids burning rate-limit budget when
# a noisy article namedrops a wall of tickers.
_MAX_TICKERS_PER_SCAN = 3


async def enrich(
    entities: dict[str, Any],
    *,
    http_client: httpx.AsyncClient | None = None,
) -> list[EnrichmentDoc]:
    """Enrich a scan with primary-source docs derived from detected entities.

    ``entities`` is a dict produced by Prompt 4's entity detection. We currently
    consume only ``entities["tickers"]`` (deduped, capped at 3). Always returns
    a list, never raises, and respects ``settings.enrichment_timeout_seconds``.
    """

    if not entities:
        return []

    tickers_raw = entities.get("tickers") or []
    seen: set[str] = set()
    tickers: list[str] = []
    for t in tickers_raw:
        if not isinstance(t, str):
            continue
        normalized = t.strip().upper()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        tickers.append(normalized)
        if len(tickers) >= _MAX_TICKERS_PER_SCAN:
            break

    if not tickers:
        return []

    settings = get_settings()
    timeout = settings.enrichment_timeout_seconds

    async def _safe_lookup(ticker: str) -> list[EnrichmentDoc]:
        try:
            return await edgar_client.lookup_recent_filings(
                ticker,
                http_client=http_client,
            )
        except Exception as exc:  # noqa: BLE001 - enrichment is best-effort
            logger.warning("EDGAR lookup raised for %s: %s", ticker, exc)
            return []

    tasks = [asyncio.create_task(_safe_lookup(t)) for t in tickers]
    try:
        done, pending = await asyncio.wait(tasks, timeout=timeout)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        raise

    # Cancel any straggler so nothing leaks past the timeout window.
    for task in pending:
        task.cancel()

    results: list[EnrichmentDoc] = []
    # Preserve input ticker order rather than completion order so callers see
    # a stable ordering across runs.
    completed = {task: idx for idx, task in enumerate(tasks) if task in done}
    for task, _ in sorted(completed.items(), key=lambda pair: pair[1]):
        try:
            docs = task.result()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Enrichment task raised: %s", exc)
            continue
        if docs:
            results.extend(docs)

    return results
