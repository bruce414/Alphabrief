"""Integration tests for project overview (scope) endpoints."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.services.scraping_policy import FetchDecision, FetchResult


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


async def _register(client, email: str) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_get_overview_unknown_project_returns_404(client):
    await _register(client, "overview-404@example.com")

    resp = await client.get(f"/api/v1/projects/{uuid4()}/overview")
    assert resp.status_code == 404
    assert resp.json()["errorCode"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_overview_returns_defaults_and_counts(client, monkeypatch):
    html = (FIXTURES / "long_article.html").read_text(encoding="utf-8")

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html"},
            content=html.encode("utf-8"),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    await _register(client, "overview-defaults@example.com")

    created = await client.post(
        "/api/v1/projects",
        json={"title": "Scope project", "kind": "COVERAGE", "description": "A thesis"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    canvas = await client.get(f"/api/v1/projects/{project_id}/canvas")
    canvas_id = canvas.json()["id"]

    el = await client.post(
        f"/api/v1/canvases/{canvas_id}/elements",
        json={
            "elementType": "TEXT",
            "title": "Note",
            "contentMarkdown": "hello",
            "contentJson": {},
            "x": 0.0,
            "y": 0.0,
            "width": 200.0,
            "height": 100.0,
            "styleJson": {},
            "provenanceKind": "MANUAL",
        },
    )
    assert el.status_code == 201

    source = await client.post(
        "/api/v1/sources",
        json={
            "sourceType": "ARTICLE_URL",
            "input": "https://example.com/overview-test",
            "projectId": project_id,
        },
    )
    assert source.status_code == 201

    resp = await client.get(f"/api/v1/projects/{project_id}/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Scope project"
    assert body["description"] == "A thesis"
    assert body["researchGoal"] is None
    assert body["researchType"] is None
    assert body["includedTopics"] == []
    assert body["excludedTopics"] == []
    assert body["targetEntities"] == []
    assert body["timeHorizon"] is None
    assert "createdAt" in body
    assert "updatedAt" in body
    assert body["status"]["totalNodes"] == 1
    assert body["status"]["totalSources"] == 1
    assert body["status"]["openQuestionsCount"] == 0
    assert body["status"]["unsupportedClaimsCount"] == 0
    assert body["status"]["updatesAvailableCount"] == 0
    assert body["status"]["lastCheckedAt"] is None


@pytest.mark.asyncio
async def test_patch_overview_updates_single_field_leaves_others(client):
    await _register(client, "overview-patch@example.com")

    created = await client.post(
        "/api/v1/projects",
        json={"title": "Patch me", "kind": "THESIS"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    first = await client.patch(
        f"/api/v1/projects/{project_id}/overview",
        json={
            "researchGoal": "Understand NVDA supply chain",
            "includedTopics": ["semiconductors"],
            "targetEntities": ["NVDA"],
        },
    )
    assert first.status_code == 200
    assert first.json()["researchGoal"] == "Understand NVDA supply chain"
    assert first.json()["includedTopics"] == ["semiconductors"]
    assert first.json()["targetEntities"] == ["NVDA"]

    second = await client.patch(
        f"/api/v1/projects/{project_id}/overview",
        json={"timeHorizon": "12m"},
    )
    assert second.status_code == 200
    out = second.json()
    assert out["timeHorizon"] == "12m"
    assert out["researchGoal"] == "Understand NVDA supply chain"
    assert out["includedTopics"] == ["semiconductors"]
    assert out["targetEntities"] == ["NVDA"]
    assert out["excludedTopics"] == []
    assert out["researchType"] is None


@pytest.mark.asyncio
async def test_patch_overview_unknown_field_rejected(client):
    await _register(client, "overview-unknown@example.com")

    project_id = (
        await client.post("/api/v1/projects", json={"title": "X", "kind": "COVERAGE"})
    ).json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{project_id}/overview",
        json={"researchGoal": "ok", "notAField": "nope"},
    )
    assert resp.status_code == 400
    assert resp.json()["errorCode"] == "INVALID_INPUT"
