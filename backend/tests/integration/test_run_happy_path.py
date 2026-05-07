"""Integration: POST /research-items/from-source happy path."""

from __future__ import annotations

import asyncio
import math

import pytest

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
async def test_run_happy_path_strict_all_segments_match_requested(
    client, monkeypatch, db_session, run_research_inline
):
    html = _build_article_html(num_paragraphs=25, words_per_paragraph=80)
    html = html.replace(
        "<article>",
        "<article><p>Nvidia stock guidance earnings revenue margin segment.</p>",
    )
    await _register(client, "happy-run@example.com")
    sid = await _create_article_source(
        client, monkeypatch, html=html, url="https://example.com/happy-run"
    )

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text

    body = {
        "sourceId": sid,
        "requestedOutputMode": "ASK",
        "analysisIntent": "MARKET_IMPACT",
        "researchScope": "RECOMMENDED_CONTEXT",
        "researchMode": "DEEP",
        "coverageMode": "FULL_SOURCE",
        "focusQuestion": "What matters?",
        "selectedSegmentIds": [],
        "selectedEntityIds": [],
        "completionStrategy": "STRICT_REQUESTED_MODE",
        "acknowledgedHighUsageWarning": True,
        "saveToResearchLog": True,
    }
    r2 = await client.post("/api/v1/research-items/from-source", json=body)
    assert r2.status_code == 201, r2.text
    rid = r2.json()["researchItemId"]

    for _ in range(200):
        g = await client.get(f"/api/v1/research-items/{rid}")
        assert g.status_code == 200
        if g.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0.05)
    else:
        raise AssertionError("research item did not complete")

    detail = g.json()
    assert detail["status"] == "COMPLETED"
    assert detail["analysisDepthSummary"]
    assert isinstance(detail["analysisDepthSummary"], list)
    for row in detail["analysisDepthSummary"]:
        assert row["requestedMode"] == "DEEP"
        assert row["actualMode"] == "DEEP"
        assert detail["outputMarkdown"]


@pytest.mark.asyncio
async def test_run_optimize_depth_split_40_40_20(
    client, monkeypatch, db_session, run_research_inline
):
    """With >=5 segments, OPTIMIZE assigns DEEP/STANDARD/QUICK in 40/40/20 buckets."""

    html = _build_article_html(num_paragraphs=40, words_per_paragraph=80)
    html = html.replace(
        "<article>",
        "<article><p>Nvidia stock price market guidance earnings revenue.</p>",
    )
    await _register(client, "opt-run@example.com")
    sid = await _create_article_source(
        client, monkeypatch, html=html, url="https://example.com/opt-run"
    )

    r = await client.post(f"/api/v1/sources/{sid}/scan", json=SCAN_REQUEST)
    assert r.status_code == 200, r.text
    seg_count = len(r.json()["segments"])
    assert seg_count >= 5

    body = {
        "sourceId": sid,
        "requestedOutputMode": "ASK",
        "analysisIntent": "MARKET_IMPACT",
        "researchScope": "RECOMMENDED_CONTEXT",
        "researchMode": "DEEP",
        "coverageMode": "FULL_SOURCE",
        "focusQuestion": None,
        "selectedSegmentIds": [],
        "selectedEntityIds": [],
        "completionStrategy": "OPTIMIZE_RESEARCH",
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

    summary = g.json()["analysisDepthSummary"]
    modes = [row["actualMode"] for row in summary]
    deep_c = sum(1 for m in modes if m == "DEEP")
    std_c = sum(1 for m in modes if m == "STANDARD")
    quick_c = sum(1 for m in modes if m == "QUICK")
    n = len(modes)

    assert deep_c == int(math.ceil(n * 0.4))
    assert std_c == int(math.ceil(n * 0.8)) - int(math.ceil(n * 0.4))
    assert quick_c == n - int(math.ceil(n * 0.8))
