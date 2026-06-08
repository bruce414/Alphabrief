"""Integration tests for cold-start onboarding endpoints."""

from __future__ import annotations

import math
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.enums import CanvasElementType, ProvenanceKind
from app.models.canvas_element import CanvasElement

_RADIAL_RADIUS = 320.0
_RADIAL_TOLERANCE = 8.0


async def _register(client, email: str) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert r.status_code == 201, r.text


async def _create_project(client) -> str:
    created = await client.post(
        "/api/v1/projects",
        json={"title": "Onboarding project", "kind": "COVERAGE", "description": "Seed"},
    )
    assert created.status_code == 201
    return created.json()["id"]


@pytest.mark.asyncio
async def test_suggest_directions_returns_three_with_starter_elements(client, monkeypatch):
    monkeypatch.setenv("ONBOARDING_USE_MOCK", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    await _register(client, "onboarding-suggest@example.com")
    project_id = await _create_project(client)

    resp = await client.post(
        f"/api/v1/projects/{project_id}/onboarding/suggest-directions",
        json={"description": "How will AI capex affect chip suppliers in 2026?"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "suggestionId" in body
    assert len(body["directions"]) == 3
    for direction in body["directions"]:
        assert direction["key"]
        assert direction["title"]
        assert direction["summary"]
        assert direction["researchGoal"]
        assert 3 <= len(direction["starterElements"]) <= 5
        for el in direction["starterElements"]:
            assert el["elementType"] == "STICKY_NOTE"
            assert el["provenanceKind"] == "AI_ONBOARDING"
            assert el["kind"] in {"CLAIM", "RISK", "EVIDENCE", "QUESTION"}
            assert el["title"]
            assert el["body"]


@pytest.mark.asyncio
async def test_suggest_directions_mock_is_deterministic(client, monkeypatch):
    monkeypatch.setenv("ONBOARDING_USE_MOCK", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    await _register(client, "onboarding-deterministic@example.com")
    project_id = await _create_project(client)

    payload = {"description": "Rates and credit spreads into 2026"}
    first = await client.post(
        f"/api/v1/projects/{project_id}/onboarding/suggest-directions",
        json=payload,
    )
    second = await client.post(
        f"/api/v1/projects/{project_id}/onboarding/suggest-directions",
        json=payload,
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["directions"] == second.json()["directions"]
    assert first.json()["suggestionId"] != second.json()["suggestionId"]


@pytest.mark.asyncio
async def test_apply_writes_scope_and_creates_canvas_elements(client, db_session, monkeypatch):
    monkeypatch.setenv("ONBOARDING_USE_MOCK", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    await _register(client, "onboarding-apply@example.com")
    project_id = await _create_project(client)

    suggest = await client.post(
        f"/api/v1/projects/{project_id}/onboarding/suggest-directions",
        json={"description": "EM consumer recovery"},
    )
    assert suggest.status_code == 200
    direction = suggest.json()["directions"][0]

    apply = await client.post(
        f"/api/v1/projects/{project_id}/onboarding/apply",
        json={"direction": direction},
    )
    assert apply.status_code == 200, apply.text
    overview = apply.json()
    assert overview["researchGoal"] == direction["researchGoal"]
    assert overview["includedTopics"] == direction["includedTopics"]
    assert overview["excludedTopics"] == direction["excludedTopics"]
    assert overview["targetEntities"] == direction["targetEntities"]
    assert overview["timeHorizon"] == direction["timeHorizon"]

    rows = list(
        (
            await db_session.execute(
                select(CanvasElement).where(
                    CanvasElement.project_id == project_id,
                    CanvasElement.provenance_kind == ProvenanceKind.AI_ONBOARDING.value,
                )
            )
        )
        .scalars()
        .all()
    )
    groups = [r for r in rows if r.element_type == CanvasElementType.GROUP.value]
    directions = [r for r in rows if r.element_type == CanvasElementType.DIRECTION.value]
    stickies = [r for r in rows if r.element_type == CanvasElementType.STICKY_NOTE.value]
    assert len(groups) == 0
    assert len(directions) == 1
    assert directions[0].title == direction["title"]
    assert directions[0].content_markdown == direction["summary"]
    assert 3 <= len(stickies) <= 5
    for sticky in stickies:
        assert sticky.content_json.get("kind") in {"CLAIM", "RISK", "EVIDENCE", "QUESTION"}
        assert sticky.title
        assert sticky.content_markdown

    cx = float(directions[0].x) + float(directions[0].width) / 2
    cy = float(directions[0].y) + float(directions[0].height) / 2
    distances = [
        math.hypot(
            float(s.x) + float(s.width) / 2 - cx,
            float(s.y) + float(s.height) / 2 - cy,
        )
        for s in stickies
    ]
    assert distances
    for distance in distances:
        assert abs(distance - _RADIAL_RADIUS) <= _RADIAL_TOLERANCE
    spread = max(distances) - min(distances)
    assert spread <= _RADIAL_TOLERANCE

    starter_count = len(direction["starterElements"])
    assert overview["status"]["totalNodes"] >= 1 + starter_count


@pytest.mark.asyncio
async def test_apply_each_call_creates_fresh_direction_and_stickies(client, db_session, monkeypatch):
    monkeypatch.setenv("ONBOARDING_USE_MOCK", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    await _register(client, "onboarding-reapply@example.com")
    project_id = await _create_project(client)

    suggest = await client.post(
        f"/api/v1/projects/{project_id}/onboarding/suggest-directions",
        json={"description": "Biotech pipeline catalysts"},
    )
    direction = suggest.json()["directions"][0]

    first = await client.post(
        f"/api/v1/projects/{project_id}/onboarding/apply",
        json={"direction": direction},
    )
    second = await client.post(
        f"/api/v1/projects/{project_id}/onboarding/apply",
        json={"direction": direction},
    )
    assert first.status_code == 200
    assert second.status_code == 200

    directions = list(
        (
            await db_session.execute(
                select(CanvasElement).where(
                    CanvasElement.project_id == project_id,
                    CanvasElement.element_type == CanvasElementType.DIRECTION.value,
                )
            )
        )
        .scalars()
        .all()
    )
    stickies = list(
        (
            await db_session.execute(
                select(CanvasElement).where(
                    CanvasElement.project_id == project_id,
                    CanvasElement.element_type == CanvasElementType.STICKY_NOTE.value,
                    CanvasElement.provenance_kind == ProvenanceKind.AI_ONBOARDING.value,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(directions) == 2
    starter_count = len(direction["starterElements"])
    assert len(stickies) == starter_count * 2


@pytest.mark.asyncio
async def test_suggest_unknown_project_returns_404(client, monkeypatch):
    monkeypatch.setenv("ONBOARDING_USE_MOCK", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    await _register(client, "onboarding-404@example.com")
    resp = await client.post(
        f"/api/v1/projects/{uuid4()}/onboarding/suggest-directions",
        json={"description": "test"},
    )
    assert resp.status_code == 404
