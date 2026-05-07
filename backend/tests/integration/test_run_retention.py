"""Integration: retention purge clears extracted_text after run."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import update

from app.models.source import Source
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
            content=b"<html><body><article><p>" + (b"w " * 400) + b"</p></article></body></html>",
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


@pytest.fixture
def run_research_inline(db_session, monkeypatch):
    async def _inline(run_id):
        from app.services.adaptive_research_service import execute_run

        await execute_run(run_id, db=db_session)

    monkeypatch.setattr(
        "app.api.v1.research_items.execute_run_in_background",
        _inline,
    )


@pytest.mark.asyncio
async def test_retention_not_stored_clears_extracted_text(
    client, monkeypatch, db_session, run_research_inline
):
    await _register(client, "ret-run@example.com")
    sid_str = await _create_article_source(
        client, monkeypatch, url="https://example.com/ret-run"
    )
    sid = uuid.UUID(sid_str)

    await db_session.execute(
        update(Source)
        .where(Source.id == sid)
        .values(
            raw_text_retention="NOT_STORED",
            extracted_text="stored body text for purge test",
            extracted_text_word_count=12,
            source_access_status="FULL_TEXT_EXTRACTED",
        )
    )
    await db_session.commit()

    r = await client.post(f"/api/v1/sources/{sid_str}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text

    body = {
        "sourceId": sid_str,
        "requestedOutputMode": "ASK",
        "analysisIntent": "MARKET_IMPACT",
        "researchScope": "RECOMMENDED_CONTEXT",
        "researchMode": "STANDARD",
        "coverageMode": "FULL_SOURCE",
        "completionStrategy": "STRICT_REQUESTED_MODE",
        "acknowledgedHighUsageWarning": True,
        "saveToResearchLog": True,
    }
    r2 = await client.post("/api/v1/research-items/from-source", json=body)
    assert r2.status_code == 201, r2.text
    rid = r2.json()["researchItemId"]

    for _ in range(200):
        g = await client.get(f"/api/v1/research-items/{rid}")
        if g.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0.05)
    else:
        raise AssertionError("timeout")

    src = await db_session.get(Source, sid)
    assert src is not None
    await db_session.refresh(src)
    assert src is not None
    assert src.extracted_text is None
    assert src.extracted_text_word_count == 0
