"""Integration tests for POST /api/v1/sources/{sourceId}/scan."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.clients import edgar_client
from app.clients.edgar_client import EnrichmentDoc
from app.services.scraping_policy import FetchDecision, FetchResult


SCAN_REQUEST = {
    "requestedOutputMode": "ASK",
    "analysisIntent": "MARKET_IMPACT",
    "researchMode": "STANDARD",
    "coverageMode": "FULL_SOURCE",
}


async def _register(client, email: str, password: str = "password123") -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text


def _build_article_html(num_paragraphs: int, words_per_paragraph: int) -> str:
    paragraphs: list[str] = []
    for p in range(num_paragraphs):
        words = " ".join(
            f"alpha{p:03d}word{w:03d}" for w in range(words_per_paragraph)
        )
        paragraphs.append(f"<p>{words}</p>")
    body = "\n".join(paragraphs)
    return (
        "<!DOCTYPE html><html><head>"
        "<meta property='og:title' content='Long Fixture Article' />"
        "<title>Long Fixture Article</title>"
        f"</head><body><article>{body}</article></body></html>"
    )


async def _create_article_source(client, monkeypatch, *, html: str, url: str):
    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=html.encode("utf-8"),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": url},
    )
    assert r.status_code == 201, r.text
    return r.json()["sourceId"]


@pytest.mark.asyncio
async def test_scan_requires_authentication(client):
    r = await client.post(
        "/api/v1/sources/00000000-0000-0000-0000-000000000000/scan",
        json=SCAN_REQUEST,
    )
    assert r.status_code == 401
    assert r.json()["errorCode"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_scan_returns_404_for_missing_source(client):
    await _register(client, "scan-missing@example.com")
    r = await client.post(
        "/api/v1/sources/00000000-0000-0000-0000-000000000000/scan",
        json=SCAN_REQUEST,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_scan_forbidden_for_non_owner(client, monkeypatch):
    html = _build_article_html(num_paragraphs=20, words_per_paragraph=100)
    await _register(client, "alice-scan@example.com")
    sid = await _create_article_source(
        client, monkeypatch, html=html, url="https://example.com/a"
    )

    await client.post("/api/v1/auth/logout")
    await _register(client, "bob-scan@example.com")
    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 403
    assert r.json()["errorCode"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_scan_article_returns_segments_topics_and_low_complexity(
    client, monkeypatch
):
    html = _build_article_html(num_paragraphs=20, words_per_paragraph=100)
    # Inject a few topical keywords / company names so detection is exercised.
    html = html.replace(
        "<article>",
        "<article><p>Nvidia and Visa earnings are influenced by Fed policy, "
        "tariffs and oil markets.</p>",
    )
    await _register(client, "scan-article@example.com")
    sid = await _create_article_source(
        client, monkeypatch, html=html, url="https://example.com/long"
    )

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sourceId"] == sid
    assert "scanId" in body
    assert body["sourceComplexity"] in {"LOW", "MEDIUM"}
    assert body["estimateConfidence"] in {"HIGH", "MEDIUM"}
    assert isinstance(body["estimatedAllowanceImpactPercent"], (int, float))
    assert body["warningLevel"] == "NONE"
    assert body["requiresWarning"] is False
    assert len(body["segments"]) >= 5

    topics = set(body["detectedTopics"])
    assert {"earnings", "Fed", "tariffs", "oil"}.issubset(topics)

    entity_names = {e["name"] for e in body["detectedEntities"]}
    assert "Nvidia" in entity_names
    assert "Visa" in entity_names


@pytest.mark.asyncio
async def test_scan_metadata_only_source_returns_synthetic_segment_and_low_confidence(
    client, monkeypatch
):
    """403/paywalled article extracts as METADATA_ONLY - scan still works."""

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=403,
            headers={"content-type": "text/html"},
            content=b"<html><title>Walled</title><body><p>x</p></body></html>",
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    await _register(client, "scan-meta@example.com")
    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/wall"},
    )
    assert r.status_code == 201
    sid = r.json()["sourceId"]

    scan_req = dict(SCAN_REQUEST)
    scan_req["researchMode"] = "QUICK"
    r = await client.post(f"/api/v1/sources/{sid}/scan", json=scan_req)
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["segments"]) == 1
    assert body["estimateConfidence"] == "LOW"
    assert body["recommendedResearchMode"] == "QUICK"


@pytest.mark.asyncio
async def test_scan_400_when_no_text_and_not_metadata_only(client, monkeypatch):
    """A FAILED-status source has no extracted_text and is not METADATA_ONLY."""

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=500,
            headers={"content-type": "text/html"},
            content=b"",
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    await _register(client, "scan-failed@example.com")
    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/dead"},
    )
    assert r.status_code == 201
    assert r.json()["sourceAccessStatus"] == "FAILED"
    sid = r.json()["sourceId"]

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 400
    assert r.json()["errorCode"] == "SOURCE_NOT_SCANNABLE"


def _make_edgar_doc(ticker: str = "NVDA") -> EnrichmentDoc:
    return EnrichmentDoc(
        source="EDGAR",
        title="10-Q — filed 2025-10-15",
        url=(
            "https://www.sec.gov/Archives/edgar/data/1045810/"
            "000104581025000123/0001045810-25-000123-index.htm"
        ),
        snippet="Quarterly report.",
        retrieved_at=datetime.now(UTC),
        metadata={"ticker": ticker, "form": "10-Q", "filed_at": "2025-10-15"},
    )


@pytest.mark.asyncio
async def test_scan_metadata_only_with_detected_ticker_returns_edgar_enrichment(
    client, monkeypatch
):
    """METADATA_ONLY source whose scan detects NVDA → enrichments[0].source == EDGAR."""

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=403,
            headers={"content-type": "text/html"},
            content=(
                b"<html><head><title>Nvidia paywall</title>"
                b"<meta name='description' content='Nvidia earnings preview' />"
                b"</head><body><p>Subscribe to read.</p></body></html>"
            ),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    docs_for_nvda = [_make_edgar_doc("NVDA")]

    async def fake_lookup(ticker: str, **kwargs):  # noqa: ANN003
        assert ticker == "NVDA"
        return list(docs_for_nvda)

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", fake_lookup)

    await _register(client, "scan-enrich-meta@example.com")
    create = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/wall"},
    )
    assert create.status_code == 201
    assert create.json()["sourceAccessStatus"] == "METADATA_ONLY"
    sid = create.json()["sourceId"]

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["enrichments"], "expected enrichments for METADATA_ONLY source"
    assert body["enrichments"][0]["source"] == "EDGAR"
    assert "10-Q" in body["enrichments"][0]["title"]
    assert body["enrichments"][0]["metadata"]["ticker"] == "NVDA"


@pytest.mark.asyncio
async def test_scan_full_text_source_does_not_run_enrichment(client, monkeypatch):
    """FULL_TEXT_EXTRACTED sources should have empty enrichments and never call EDGAR."""

    html = _build_article_html(num_paragraphs=20, words_per_paragraph=100)
    html = html.replace(
        "<article>",
        "<article><p>Nvidia results were strong this quarter.</p>",
    )

    calls = {"count": 0}

    async def fake_lookup(ticker: str, **kwargs):  # noqa: ANN003
        calls["count"] += 1
        return [_make_edgar_doc(ticker)]

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", fake_lookup)

    await _register(client, "scan-enrich-full@example.com")
    sid = await _create_article_source(
        client, monkeypatch, html=html, url="https://example.com/full"
    )

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["enrichments"] == []
    assert calls["count"] == 0


@pytest.mark.asyncio
async def test_scan_metadata_only_extracts_entities_from_url_slug(client, monkeypatch):
    """Paywalled article whose title is just 'Subscribe ...' should still
    surface AAPL because the URL slug contains 'apple-stock-...'."""

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        # Schema.org isAccessibleForFree=False marks the page as paywalled,
        # tripping the post-fetch policy gate to METADATA_ONLY.
        body = (
            "<html><head>"
            "<title>Subscribe to Barron's</title>"
            "<script type='application/ld+json'>"
            '{"@type":"NewsArticle","isAccessibleForFree":false}'
            "</script>"
            "</head><body><p>Subscribers only.</p></body></html>"
        )
        return FetchResult(
            final_url=start_url,
            domain="www.barrons.com",
            decision=FetchDecision.METADATA_ONLY,
            reason="paywall_detected",
            status_code=200,
            headers={"content-type": "text/html"},
            content=body.encode("utf-8"),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    captured: list[str] = []

    async def fake_lookup(ticker: str, **kwargs):  # noqa: ANN003
        captured.append(ticker)
        return [_make_edgar_doc(ticker)]

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", fake_lookup)

    await _register(client, "scan-slug-fallback@example.com")
    create = await client.post(
        "/api/v1/sources",
        json={
            "sourceType": "ARTICLE_URL",
            "input": (
                "https://www.barrons.com/articles/"
                "apple-stock-record-track-june-5a777ea2"
            ),
        },
    )
    assert create.status_code == 201
    assert create.json()["sourceAccessStatus"] == "METADATA_ONLY"
    sid = create.json()["sourceId"]

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    body = r.json()

    entity_tickers = {e["ticker"] for e in body["detectedEntities"] if e.get("ticker")}
    assert "AAPL" in entity_tickers
    assert captured == ["AAPL"]
    assert body["enrichments"], "expected EDGAR enrichment for AAPL"
    assert body["enrichments"][0]["metadata"]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_scan_metadata_only_without_detected_entities_returns_empty_enrichments(
    client, monkeypatch
):
    """No detected tickers → EDGAR is never called and enrichments == []."""

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=403,
            headers={"content-type": "text/html"},
            content=(
                b"<html><head><title>Generic news</title></head>"
                b"<body><p>No tickers here.</p></body></html>"
            ),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    calls = {"count": 0}

    async def fake_lookup(ticker: str, **kwargs):  # noqa: ANN003
        calls["count"] += 1
        return [_make_edgar_doc(ticker)]

    monkeypatch.setattr(edgar_client, "lookup_recent_filings", fake_lookup)

    await _register(client, "scan-enrich-empty@example.com")
    create = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/blank"},
    )
    assert create.status_code == 201
    assert create.json()["sourceAccessStatus"] == "METADATA_ONLY"
    sid = create.json()["sourceId"]

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["enrichments"] == []
    assert calls["count"] == 0


@pytest.mark.asyncio
async def test_scan_youtube_source_segments_30_minute_transcript(client, monkeypatch):
    """A 30-minute transcript should yield 6-10 windows."""

    async def fake_oembed(url: str, **kwargs):  # noqa: ANN003
        return {"title": "Video", "author_name": "Channel"}

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_oembed",
        fake_oembed,
    )
    # 30 min at 150 wpm ≈ 4500 words.
    transcript = " ".join(["nvidia"] * 4500)
    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_transcript_text",
        AsyncMock(return_value=transcript),
    )

    await _register(client, "scan-yt@example.com")
    r = await client.post(
        "/api/v1/sources",
        json={
            "sourceType": "YOUTUBE_URL",
            "input": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        },
    )
    assert r.status_code == 201

    sid = r.json()["sourceId"]
    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    body = r.json()
    assert 6 <= len(body["segments"]) <= 10
    for seg in body["segments"]:
        assert seg["startOffsetSeconds"] is not None
        assert seg["endOffsetSeconds"] is not None
