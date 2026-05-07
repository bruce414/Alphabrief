"""Unit tests for the SEC EDGAR submissions JSON client."""

from __future__ import annotations

import json

import httpx
import pytest

from app.clients import edgar_client
from app.clients.edgar_client import (
    lookup_recent_filings,
    reset_cik_cache_state,
    reset_rate_limit_state,
)
from app.core.config import get_settings


TICKER_MAP_FIXTURE = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
}

SUBMISSIONS_FIXTURE = {
    "cik": "1045810",
    "name": "NVIDIA CORP",
    "tickers": ["NVDA"],
    "filings": {
        "recent": {
            "accessionNumber": [
                "0001045810-25-000300",
                "0001045810-25-000250",
                "0001045810-25-000200",
                "0001045810-25-000190",
                "0001045810-25-000180",
                "0001045810-25-000170",
                "0001045810-25-000160",
                "0001045810-25-000150",
                "0001045810-25-000140",
            ],
            "form": [
                "10-Q",
                "8-K",
                "DEF 14A",
                "SC 13G",
                "4",
                "4",
                "4",
                "144",
                "S-3",
            ],
            "filingDate": [
                "2025-10-15",
                "2025-10-01",
                "2025-09-15",
                "2025-09-10",
                "2025-10-14",
                "2025-10-13",
                "2025-10-12",
                "2025-10-11",
                "2025-08-01",
            ],
            "primaryDocument": [
                "nvda-20250930.htm",
                "nvda-8k.htm",
                "proxy.htm",
                "sc13g.htm",
                "xslF345.htm",
                "xslF345_2.htm",
                "xslF345_3.htm",
                "form144.htm",
                "s3.htm",
            ],
        }
    },
}


@pytest.fixture(autouse=True)
def _reset_state():
    reset_rate_limit_state()
    reset_cik_cache_state()
    yield
    reset_rate_limit_state()
    reset_cik_cache_state()


@pytest.mark.asyncio
async def test_lookup_recent_filings_categories_and_default_filtering():
    captured: list[httpx.Request] = []
    calls = {"ticker_map": 0, "submissions": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/files/company_tickers.json":
            calls["ticker_map"] += 1
            return httpx.Response(
                200,
                text=json.dumps(TICKER_MAP_FIXTURE),
                headers={"content-type": "application/json"},
            )
        if request.url.host == "data.sec.gov" and request.url.path.startswith(
            "/submissions/CIK"
        ):
            calls["submissions"] += 1
            return httpx.Response(
                200,
                text=json.dumps(SUBMISSIONS_FIXTURE),
                headers={"content-type": "application/json"},
            )
        raise AssertionError(f"unexpected request: {request.url!s}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings(
            "NVDA",
            categories=["PERIODIC", "GOVERNANCE", "OWNERSHIP"],
            http_client=client,
        )

    categories = {d.category for d in docs}
    assert "PERIODIC" in categories
    assert "GOVERNANCE" in categories
    assert "OWNERSHIP" in categories
    assert "INSIDER" not in categories
    assert "CAPITAL_RAISE" not in categories

    # Ordering: category priority, then filing date desc within each category.
    assert docs[0].category == "PERIODIC"
    assert docs[0].metadata["form"] == "10-Q"
    assert docs[0].metadata["filed_at"] == "2025-10-15"

    # User-Agent must be present on both requests (SEC rejects without one).
    ua = get_settings().scraping_user_agent
    assert any(r.headers.get("user-agent") == ua for r in captured)
    assert all(r.headers.get("user-agent") == ua for r in captured)

    assert calls["ticker_map"] == 1
    assert calls["submissions"] == 1


@pytest.mark.asyncio
async def test_lookup_recent_filings_unknown_ticker_returns_empty_and_skips_submissions():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/files/company_tickers.json":
            return httpx.Response(
                200,
                text=json.dumps(TICKER_MAP_FIXTURE),
                headers={"content-type": "application/json"},
            )
        raise AssertionError(f"unexpected request: {request.url!s}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("ZZZZ", http_client=client)
    assert docs == []
    assert any(r.url.path == "/files/company_tickers.json" for r in captured)
    assert not any(r.url.host == "data.sec.gov" for r in captured)


@pytest.mark.asyncio
async def test_lookup_recent_filings_submissions_404_returns_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/files/company_tickers.json":
            return httpx.Response(
                200,
                text=json.dumps(TICKER_MAP_FIXTURE),
                headers={"content-type": "application/json"},
            )
        if request.url.host == "data.sec.gov":
            return httpx.Response(404, text="not found")
        raise AssertionError(f"unexpected request: {request.url!s}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("NVDA", http_client=client)
    assert docs == []


@pytest.mark.asyncio
async def test_lookup_recent_filings_mismatched_parallel_arrays_returns_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/files/company_tickers.json":
            return httpx.Response(
                200,
                text=json.dumps(TICKER_MAP_FIXTURE),
                headers={"content-type": "application/json"},
            )
        if request.url.host == "data.sec.gov":
            bad = json.loads(json.dumps(SUBMISSIONS_FIXTURE))
            bad["filings"]["recent"]["form"] = bad["filings"]["recent"]["form"][:-1]
            return httpx.Response(
                200,
                text=json.dumps(bad),
                headers={"content-type": "application/json"},
            )
        raise AssertionError(f"unexpected request: {request.url!s}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("NVDA", http_client=client)
    assert docs == []


@pytest.mark.asyncio
async def test_lookup_recent_filings_per_category_cap_respected_for_insider():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/files/company_tickers.json":
            return httpx.Response(
                200,
                text=json.dumps(TICKER_MAP_FIXTURE),
                headers={"content-type": "application/json"},
            )
        if request.url.host == "data.sec.gov":
            # add extra Form 4s to ensure cap works
            fixture = json.loads(json.dumps(SUBMISSIONS_FIXTURE))
            recent = fixture["filings"]["recent"]
            for k in ("accessionNumber", "form", "filingDate", "primaryDocument"):
                assert isinstance(recent[k], list)
            for i in range(5):
                recent["accessionNumber"].append(f"0001045810-25-0099{i}0")
                recent["form"].append("4")
                recent["filingDate"].append(f"2025-10-0{i+1}")
                recent["primaryDocument"].append(f"xslF345_extra_{i}.htm")
            return httpx.Response(
                200,
                text=json.dumps(fixture),
                headers={"content-type": "application/json"},
            )
        raise AssertionError(f"unexpected request: {request.url!s}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings(
            "NVDA",
            categories=["INSIDER"],
            limit_per_category=3,
            http_client=client,
        )
    assert len(docs) == 3
    assert all(d.category == "INSIDER" for d in docs)


@pytest.mark.asyncio
async def test_lookup_recent_filings_empty_ticker_short_circuits(monkeypatch):
    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(200, text="{}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs = await lookup_recent_filings("", http_client=client)
    assert docs == []
    assert called["count"] == 0


@pytest.mark.asyncio
async def test_cik_cache_reused_across_calls():
    calls = {"ticker_map": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/files/company_tickers.json":
            calls["ticker_map"] += 1
            return httpx.Response(
                200,
                text=json.dumps(TICKER_MAP_FIXTURE),
                headers={"content-type": "application/json"},
            )
        if request.url.host == "data.sec.gov":
            return httpx.Response(
                200,
                text=json.dumps(SUBMISSIONS_FIXTURE),
                headers={"content-type": "application/json"},
            )
        raise AssertionError(f"unexpected request: {request.url!s}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        docs1 = await lookup_recent_filings("NVDA", http_client=client)
        docs2 = await lookup_recent_filings("NVDA", http_client=client)

    assert docs1
    assert docs2
    assert calls["ticker_map"] == 1
