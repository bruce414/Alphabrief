"""Integration: scan required before /from-source."""

from __future__ import annotations

import pytest

from app.services.scraping_policy import FetchDecision, FetchResult


async def _register(client, email: str, password: str = "password123") -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text


async def _create_article_source(client, monkeypatch, *, url: str):
    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><body><article><p>ok</p></article></body></html>",
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
async def test_run_scan_required_first(client, monkeypatch):
    await _register(client, "scan-req@example.com")
    sid = await _create_article_source(
        client, monkeypatch, url="https://example.com/scan-req"
    )

    body = {
        "sourceId": sid,
        "requestedOutputMode": "ASK",
        "analysisIntent": "MARKET_IMPACT",
        "researchScope": "RECOMMENDED_CONTEXT",
        "researchMode": "STANDARD",
        "coverageMode": "FULL_SOURCE",
        "completionStrategy": "STRICT_REQUESTED_MODE",
        "acknowledgedHighUsageWarning": True,
        "saveToResearchLog": True,
    }
    r = await client.post("/api/v1/research-items/from-source", json=body)
    assert r.status_code == 400
    assert r.json()["errorCode"] == "SCAN_REQUIRED_FIRST"
