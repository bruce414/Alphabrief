"""Integration tests for project memory endpoints."""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.core.enums import ChatTurnRole, ChatTurnStatus, MemoryUpdatedBy
from app.models.chat_turn import ChatTurn
from app.models.project_memory import ProjectMemory
from app.models.usage_event import UsageEvent
from app.repositories.chat_turn_repository import ChatTurnRepository


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
async def test_post_memory_refresh_no_activity_without_turns(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "pmem-refresh-empty@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/memory/refresh",
        json={"source": "RECENT_ACTIVITY", "maxActivityItems": 30},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "NO_ACTIVITY"
    assert payload["memoryRefreshJobId"]

    mem_count = (
        await db_session.execute(
            select(func.count()).select_from(UsageEvent).where(UsageEvent.event_type == "MEMORY_UPDATE")
        )
    ).scalar_one()
    assert int(mem_count or 0) == 0


@pytest.mark.asyncio
async def test_post_memory_refresh_completed_with_mock_ai(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "pmem-refresh-ai@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    me = await client.get("/api/v1/me")
    assert me.status_code == 200
    user_id = UUID(me.json()["id"])

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    proj = await client.get(f"/api/v1/projects/{project_id}")
    assert proj.status_code == 200
    project_title = proj.json()["title"]

    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "Research"})
    assert chat.status_code == 201
    chat_id = UUID(chat.json()["id"])

    turn_repo = ChatTurnRepository(db_session)
    await turn_repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=0,
            role=ChatTurnRole.USER.value,
            status=ChatTurnStatus.COMPLETED.value,
            content_markdown="What about NVDA supply chain?",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )
    await turn_repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=1,
            role=ChatTurnRole.ASSISTANT.value,
            status=ChatTurnStatus.COMPLETED.value,
            content_markdown="TSMC is a key supplier.",
            content_json=None,
            model_provider="mock",
            model_name="mock-model",
        )
    )

    resp = await client.post(
        f"/api/v1/projects/{project_id}/memory/refresh",
        json={"source": "RECENT_ACTIVITY", "maxActivityItems": 30},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["memoryRefreshJobId"]

    mem = await client.get(f"/api/v1/projects/{project_id}/memory")
    assert mem.status_code == 200
    mjson = mem.json()
    assert mjson["summaryMarkdown"] == f"Mock memory summary for {project_title}"
    assert mjson["entities"] == ["MOCK"]
    assert mjson["themes"] == ["mock-theme"]
    assert mjson["openQuestions"] == ["What is the next milestone?"]
    assert mjson["conclusions"] == []
    assert mjson["id"] == body["memoryRefreshJobId"]

    row = (
        await db_session.execute(select(ProjectMemory).where(ProjectMemory.project_id == UUID(project_id)))
    ).scalar_one()
    assert row.updated_by == MemoryUpdatedBy.AI.value

    mem_events = (
        await db_session.execute(select(func.count()).select_from(UsageEvent).where(UsageEvent.event_type == "MEMORY_UPDATE"))
    ).scalar_one()
    assert int(mem_events or 0) >= 1
