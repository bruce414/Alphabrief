"""Integration: usage_events recorded per analyzed segment."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import func, select

from app.models.usage_event import UsageEvent
from app.services.scraping_policy import FetchDecision, FetchResult


async def _register(client, email: str, password: str = "password123") -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text


def _html() -> str:
    parts = [f"<p>{'word ' * 50}</p>" for _ in range(20)]
    return (
        "<!DOCTYPE html><html><body><article>"
        + "".join(parts)
        + "</article></body></html>"
    )


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
async def test_usage_events_per_segment(client, monkeypatch, db_session, run_research_inline):
    await _register(client, "usage-run@example.com")
    sid = await _create_article_source(
        client, monkeypatch, url="https://example.com/usage-run"
    )

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    seg_n = len(r.json()["segments"])
    assert seg_n >= 1

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
    r2 = await client.post("/api/v1/research-items/from-source", json=body)
    assert r2.status_code == 201, r2.text
    rid = uuid.UUID(r2.json()["researchItemId"])

    for _ in range(200):
        g = await client.get(f"/api/v1/research-items/{rid}")
        if g.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0.05)
    else:
        raise AssertionError("timeout")

    n = await db_session.scalar(
        select(func.count())
        .select_from(UsageEvent)
        .where(
            UsageEvent.research_item_id == rid,
            UsageEvent.event_type == "SEGMENT_ANALYSIS",
        )
    )
    assert n == seg_n
    rows = (
        (
            await db_session.execute(
                select(UsageEvent).where(
                    UsageEvent.research_item_id == rid,
                    UsageEvent.event_type == "SEGMENT_ANALYSIS",
                )
            )
        )
        .scalars()
        .all()
    )
    assert all((e.input_tokens or 0) > 0 for e in rows)
    assert all((e.output_tokens or 0) > 0 for e in rows)
