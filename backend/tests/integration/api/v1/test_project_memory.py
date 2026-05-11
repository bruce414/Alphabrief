"""Integration tests for project memory endpoints."""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.enums import MemoryUpdatedBy
from app.models.project_memory import ProjectMemory


@pytest.mark.asyncio
async def test_get_memory_lazy_creates_empty_row(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "pmem-get@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    first = await client.get(f"/api/v1/projects/{project_id}/memory")
    assert first.status_code == 200
    body = first.json()
    assert body["projectId"] == project_id
    assert body["entities"] == []
    assert body["themes"] == []
    assert body["openQuestions"] == []
    assert body["conclusions"] == []

    row = (
        await db_session.execute(select(ProjectMemory).where(ProjectMemory.project_id == UUID(project_id)))
    ).scalar_one()
    assert row.id == UUID(body["id"])


@pytest.mark.asyncio
async def test_patch_memory_updates_fields_and_sets_updated_by_user(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "pmem-patch@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    patched = await client.patch(
        f"/api/v1/projects/{project_id}/memory",
        json={
            "summaryMarkdown": "## Thesis\n\nUpdated.",
            "entities": ["NVDA", "AMD"],
            "themes": ["AI infra"],
            "openQuestions": ["Durability?"],
            "conclusions": [],
        },
    )
    assert patched.status_code == 200
    out = patched.json()
    assert out["summaryMarkdown"] == "## Thesis\n\nUpdated."
    assert out["entities"] == ["NVDA", "AMD"]
    assert out["themes"] == ["AI infra"]
    assert out["openQuestions"] == ["Durability?"]
    assert out["conclusions"] == []

    row = (
        await db_session.execute(select(ProjectMemory).where(ProjectMemory.project_id == UUID(project_id)))
    ).scalar_one()
    assert row.updated_by == MemoryUpdatedBy.USER.value


@pytest.mark.asyncio
async def test_post_memory_refresh_returns_501(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "pmem-501@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/memory/refresh",
        json={"source": "RECENT_ACTIVITY", "maxActivityItems": 30},
    )
    assert resp.status_code == 501
    payload = resp.json()
    assert payload["error"]["code"] == "NOT_IMPLEMENTED"
    assert "not available" in payload["error"]["message"].lower()
