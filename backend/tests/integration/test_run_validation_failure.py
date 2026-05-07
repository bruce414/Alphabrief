"""Integration: validation failures mark segment FAILED but run COMPLETED."""

from __future__ import annotations

import asyncio

import pytest

from app.clients.ai_provider_client import SegmentAnalysisResult
from app.services.scraping_policy import FetchDecision, FetchResult


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
        "<!DOCTYPE html><html><head><title>t</title></head>"
        f"<body><article>{body}</article></body></html>"
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


SCAN_REQUEST = {
    "requestedOutputMode": "ASK",
    "analysisIntent": "MARKET_IMPACT",
    "researchMode": "STANDARD",
    "coverageMode": "FULL_SOURCE",
}


class InvalidTwiceProvider:
    async def generate_segment_analysis(self, prompt: str, *, depth):  # noqa: ANN001
        return SegmentAnalysisResult(
            analysis_markdown="{}",
            analysis_json={},
            key_entities=None,
            key_topics=None,
            confidence_label="INVALID",
            input_tokens=1,
            output_tokens=1,
        )


@pytest.fixture
def run_research_inline_bad_ai(db_session, monkeypatch):
    async def _inline(run_id):
        from app.services import adaptive_research_service as ars

        await ars.execute_run(
            run_id,
            db=db_session,
            ai_provider=InvalidTwiceProvider(),
        )

    monkeypatch.setattr(
        "app.api.v1.research_items.execute_run_in_background",
        _inline,
    )


@pytest.mark.asyncio
async def test_validation_failure_segment_failed_run_completed(
    client, monkeypatch, db_session, run_research_inline_bad_ai
):
    html = _build_article_html(num_paragraphs=15, words_per_paragraph=60)
    await _register(client, "val-run@example.com")
    sid = await _create_article_source(
        client, monkeypatch, html=html, url="https://example.com/val-run"
    )

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text

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
    rid = r2.json()["researchItemId"]
    run_id = r2.json()["analysisRunId"]

    for _ in range(200):
        g = await client.get(f"/api/v1/research-items/{rid}")
        if g.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0.05)
    else:
        raise AssertionError("timeout")

    segs = await client.get(f"/api/v1/analysis-runs/{run_id}/segments")
    assert segs.status_code == 200
    items = segs.json()["items"]
    assert any(x["status"] == "FAILED" for x in items)
