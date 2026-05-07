"""Unit tests for the source enrichment service (PR #5)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from app.clients import edgar_client
from app.clients.edgar_client import EnrichmentDoc
from app.core.config import get_settings
from app.services import enrichment_service


def _make_doc(ticker: str, form: str = "10-Q") -> EnrichmentDoc:
    return EnrichmentDoc(
        source="EDGAR",
        title=f"{form} — filed 2025-10-15",
        url=f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={ticker}",
        snippet=None,
        retrieved_at=datetime.now(UTC),
        metadata={"ticker": ticker, "form": form},
    )


@pytest.mark.asyncio
async def test_enrich_returns_docs_for_single_ticker(monkeypatch):
    expected = [_make_doc("NVDA"), _make_doc("NVDA", form="8-K")]

    async def fake_lookup(ticker: str, **kwargs):  # noqa: ANN003
        assert ticker == "NVDA"
        return expected

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", fake_lookup)
    docs = await enrichment_service.enrich({"tickers": ["NVDA"]})
    assert docs == expected


@pytest.mark.asyncio
async def test_enrich_empty_entities_makes_no_calls(monkeypatch):
    calls = {"count": 0}

    async def fake_lookup(ticker: str, **kwargs):  # noqa: ANN003
        calls["count"] += 1
        return []

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", fake_lookup)

    assert await enrichment_service.enrich({}) == []
    assert await enrichment_service.enrich({"tickers": []}) == []
    assert await enrichment_service.enrich({"tickers": [None, "", "  "]}) == []
    assert calls["count"] == 0


@pytest.mark.asyncio
async def test_enrich_caps_at_first_three_tickers(monkeypatch):
    seen: list[str] = []

    async def fake_lookup(ticker: str, **kwargs):  # noqa: ANN003
        seen.append(ticker)
        return [_make_doc(ticker)]

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", fake_lookup)

    docs = await enrichment_service.enrich(
        {"tickers": ["NVDA", "AAPL", "MSFT", "GOOGL", "META"]}
    )
    assert seen == ["NVDA", "AAPL", "MSFT"]
    assert len(docs) == 3


@pytest.mark.asyncio
async def test_enrich_dedups_and_uppercases_tickers(monkeypatch):
    seen: list[str] = []

    async def fake_lookup(ticker: str, **kwargs):  # noqa: ANN003
        seen.append(ticker)
        return [_make_doc(ticker)]

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", fake_lookup)

    docs = await enrichment_service.enrich(
        {"tickers": ["nvda", "NVDA", "  nvda  ", "AAPL"]}
    )
    assert seen == ["NVDA", "AAPL"]
    assert len(docs) == 2


@pytest.mark.asyncio
async def test_enrich_returns_within_timeout_when_lookup_hangs(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "enrichment_timeout_seconds", 0.1)

    async def slow_lookup(ticker: str, **kwargs):  # noqa: ANN003
        await asyncio.sleep(2.0)
        return [_make_doc(ticker)]

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", slow_lookup)

    started = asyncio.get_event_loop().time()
    docs = await enrichment_service.enrich({"tickers": ["NVDA"]})
    elapsed = asyncio.get_event_loop().time() - started
    assert docs == []
    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_enrich_returns_partial_results_on_timeout(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "enrichment_timeout_seconds", 0.2)

    fast_doc = _make_doc("NVDA")

    async def selective_lookup(ticker: str, **kwargs):  # noqa: ANN003
        if ticker == "NVDA":
            return [fast_doc]
        await asyncio.sleep(2.0)
        return [_make_doc(ticker)]

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", selective_lookup)

    docs = await enrichment_service.enrich({"tickers": ["NVDA", "AAPL"]})
    assert docs == [fast_doc]


@pytest.mark.asyncio
async def test_enrich_one_lookup_raising_does_not_drop_others(monkeypatch):
    nvda_doc = _make_doc("NVDA")
    msft_doc = _make_doc("MSFT")

    async def flaky_lookup(ticker: str, **kwargs):  # noqa: ANN003
        if ticker == "AAPL":
            raise RuntimeError("boom")
        if ticker == "NVDA":
            return [nvda_doc]
        if ticker == "MSFT":
            return [msft_doc]
        return []

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", flaky_lookup)

    docs = await enrichment_service.enrich(
        {"tickers": ["NVDA", "AAPL", "MSFT"]}
    )
    assert nvda_doc in docs
    assert msft_doc in docs
    assert len(docs) == 2
