"""Integration tests for auto-created DIRECTION canvas nodes after first chat title."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select

from app.core.enums import CanvasElementType, ProvenanceKind
from app.models.canvas_element import CanvasElement


async def _register(client, email: str) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert r.status_code == 201, r.text


async def _poll_assistant_completed(client, asst_turn_id: str) -> None:
    for _ in range(25):
        got = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
        assert got.status_code == 200
        if got.json()["status"] == "COMPLETED":
            return
        await asyncio.sleep(0)
    got = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
    assert got.json()["status"] == "COMPLETED"


async def _direction_count(db_session, project_id: str) -> int:
    result = await db_session.execute(
        select(func.count())
        .select_from(CanvasElement)
        .where(
            CanvasElement.project_id == project_id,
            CanvasElement.element_type == CanvasElementType.DIRECTION.value,
            CanvasElement.archived_at.is_(None),
        )
    )
    return int(result.scalar_one())


@pytest.mark.asyncio
async def test_first_chat_title_creates_direction_element(client, db_session):
    await _register(client, "direction-autocreate@example.com")
    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    chat_id = chat.json()["id"]

    user_message = "What drives NVDA margin expansion in 2026?"
    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": user_message})
    assert sent.status_code == 200
    await _poll_assistant_completed(client, sent.json()["assistantTurnId"])

    got = await client.get(f"/api/v1/chats/{chat_id}")
    chat_title = got.json()["chat"]["title"]
    assert chat_title != "New chat"

    assert await _direction_count(db_session, project_id) == 1

    direction = (
        await db_session.execute(
            select(CanvasElement).where(
                CanvasElement.project_id == project_id,
                CanvasElement.element_type == CanvasElementType.DIRECTION.value,
            )
        )
    ).scalar_one()
    assert direction.title == chat_title
    assert direction.provenance_kind == ProvenanceKind.AI_AUTO_DIRECTION.value
    assert direction.content_markdown == ""


@pytest.mark.asyncio
async def test_second_chat_title_does_not_duplicate_direction(client, db_session):
    await _register(client, "direction-no-dup@example.com")
    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    chat_a = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    sent_a = await client.post(
        f"/api/v1/chats/{chat_a.json()['id']}/turns",
        json={"content": "First chat about semiconductor supply chains"},
    )
    assert sent_a.status_code == 200
    await _poll_assistant_completed(client, sent_a.json()["assistantTurnId"])
    assert await _direction_count(db_session, project_id) == 1

    chat_b = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    sent_b = await client.post(
        f"/api/v1/chats/{chat_b.json()['id']}/turns",
        json={"content": "Second chat about credit spreads and refinancing"},
    )
    assert sent_b.status_code == 200
    await _poll_assistant_completed(client, sent_b.json()["assistantTurnId"])

    assert await _direction_count(db_session, project_id) == 1

    renamed = await client.patch(
        f"/api/v1/chats/{chat_a.json()['id']}",
        json={"title": "Renamed research thread"},
    )
    assert renamed.status_code == 200
    assert await _direction_count(db_session, project_id) == 1
