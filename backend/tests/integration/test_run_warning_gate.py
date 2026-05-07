"""Integration: warning gate on POST /research-items/from-source."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import update

from app.models.source import Source
from app.models.source_scan import SourceScan
from app.services.scraping_policy import FetchDecision, FetchResult


async def _register(client, email: str, password: str = "password123") -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text


def _html() -> str:
    return "<!DOCTYPE html><html><body><article><p>x</p></article></body></html>"


async def _create_article_source(client, monkeypatch, *, url: str):
    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=_html().encode("utf-8"),
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


SCAN_REQUEST = {
    "requestedOutputMode": "ASK",
    "analysisIntent": "MARKET_IMPACT",
    "researchMode": "STANDARD",
    "coverageMode": "FULL_SOURCE",
}


@pytest.mark.asyncio
async def test_run_warning_not_acknowledged_returns_400(client, monkeypatch, db_session):
    await _register(client, "warn-run@example.com")
    sid = await _create_article_source(
        client, monkeypatch, url="https://example.com/warn-run"
    )

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    scan_id = uuid.UUID(r.json()["scanId"])

    await db_session.execute(
        update(SourceScan)
        .where(SourceScan.id == scan_id)
        .values(requires_warning=True, estimated_allowance_impact_percent=55)
    )
    await db_session.execute(
        update(Source).where(Source.id == uuid.UUID(sid)).values(
            source_access_status="FULL_TEXT_EXTRACTED"
        )
    )
    await db_session.commit()

    body = {
        "sourceId": sid,
        "requestedOutputMode": "ASK",
        "analysisIntent": "MARKET_IMPACT",
        "researchScope": "RECOMMENDED_CONTEXT",
        "researchMode": "STANDARD",
        "coverageMode": "FULL_SOURCE",
        "completionStrategy": "STRICT_REQUESTED_MODE",
        "acknowledgedHighUsageWarning": False,
        "saveToResearchLog": True,
    }
    r2 = await client.post("/api/v1/research-items/from-source", json=body)
    assert r2.status_code == 400
    assert r2.json()["errorCode"] == "WARNING_NOT_ACKNOWLEDGED"
