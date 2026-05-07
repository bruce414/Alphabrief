"""Unit tests for the SEC EDGAR atom-feed client."""

from __future__ import annotations

import httpx
import pytest

from app.clients import edgar_client
from app.clients.edgar_client import lookup_recent_filings, reset_rate_limit_state
from app.core.config import get_settings


ATOM_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>NVIDIA CORP filings</title>
  <updated>2025-10-15T13:00:00-04:00</updated>
  <entry>
    <title>10-Q</title>
    <link rel="alternate" type="text/html"
          href="https://www.sec.gov/Archives/edgar/data/1045810/000104581025000123/0001045810-25-000123-index.htm" />
    <category term="10-Q" />
    <updated>2025-10-15T13:00:00-04:00</updated>
    <summary>Quarterly report.</summary>
  </entry>
  <entry>
    <title>8-K</title>
    <link rel="alternate" type="text/html"
          href="https://www.sec.gov/Archives/edgar/data/1045810/000104581025000110/0001045810-25-000110-index.htm" />
    <category term="8-K" />
    <updated>2025-09-30T11:30:00-04:00</updated>
    <summary>Current report.</summary>
  </entry>
</feed>
"""


@pytest.fixture(autouse=True)
def _reset_state():
    reset_rate_limit_state()
    yield
    reset_rate_limit_state()


@pytest.mark.asyncio
async def test_lookup_recent_filings_parses_two_entries():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            text=ATOM_FIXTURE,
            headers={"content-type": "application/atom+xml"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("NVDA", http_client=client)

    assert len(docs) == 2

    first, second = docs
    assert first.source == "EDGAR"
    assert "10-Q" in first.title
    assert "filed 2025-10-15" in first.title
    assert first.url.startswith("https://www.sec.gov/Archives/edgar/data/")
    assert first.metadata["ticker"] == "NVDA"
    assert first.metadata["form"] == "10-Q"
    assert first.metadata["filed_at"] == "2025-10-15"
    assert first.metadata.get("accession_number") == "0001045810-25-000123"

    assert second.source == "EDGAR"
    assert "8-K" in second.title
    assert second.metadata["form"] == "8-K"

    assert len(captured) == 1
    req = captured[0]
    # User-Agent must be present (EDGAR rejects requests without one).
    ua = req.headers.get("user-agent")
    assert ua and ua == get_settings().scraping_user_agent
    assert req.url.path == "/cgi-bin/browse-edgar"
    assert req.url.params.get("CIK") == "NVDA"
    assert req.url.params.get("output") == "atom"


@pytest.mark.asyncio
async def test_lookup_recent_filings_swallows_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("NVDA", http_client=client)
    assert docs == []


@pytest.mark.asyncio
async def test_lookup_recent_filings_returns_empty_for_429():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="rate limited")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("NVDA", http_client=client)
    assert docs == []


@pytest.mark.asyncio
async def test_lookup_recent_filings_handles_malformed_xml():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="<not><well-formed>xml",
            headers={"content-type": "application/atom+xml"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("NVDA", http_client=client)
    assert docs == []


@pytest.mark.asyncio
async def test_lookup_recent_filings_respects_limit():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=ATOM_FIXTURE,
            headers={"content-type": "application/atom+xml"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("NVDA", limit=1, http_client=client)
    assert len(docs) == 1


@pytest.mark.asyncio
async def test_lookup_recent_filings_empty_ticker_short_circuits(monkeypatch):
    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(200, text=ATOM_FIXTURE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("", http_client=client)
    assert docs == []
    assert called["count"] == 0
