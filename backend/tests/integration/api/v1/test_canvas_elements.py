"""Integration tests for Canvas element endpoints (manual, from-turn, from-source, patch, delete, list)."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.core.enums import ChatTurnRole, ChatTurnStatus
from app.models.chat_turn import ChatTurn
from app.models.source import Source
from app.repositories.chat_turn_repository import ChatTurnRepository


@pytest.mark.asyncio
async def test_post_manual_element_persists_and_lists(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cel-manual@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    canvas = await client.get(f"/api/v1/projects/{project_id}/canvas")
    canvas_id = canvas.json()["id"]

    created = await client.post(
        f"/api/v1/canvases/{canvas_id}/elements",
        json={
            "elementType": "TEXT",
            "title": "Note",
            "contentMarkdown": "hello",
            "contentJson": {},
            "x": 10.5,
            "y": 20.25,
            "width": 300.0,
            "height": 120.0,
            "styleJson": {},
            "provenanceKind": "MANUAL",
        },
    )
    assert created.status_code == 201
    el = created.json()
    assert el["elementType"] == "TEXT"
    assert el["x"] == 10.5
    assert el["y"] == 20.25
    assert el["width"] == 300.0
    assert el["height"] == 120.0
    el_id = el["id"]

    listed = await client.get(f"/api/v1/canvases/{canvas_id}/elements")
    assert listed.status_code == 200
    ids = [i["id"] for i in listed.json()["items"]]
    assert el_id in ids


@pytest.mark.asyncio
async def test_post_from_turn_rejects_cross_project_turn(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cel-turn-xp@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    me = await client.get("/api/v1/me")
    user_id = UUID(me.json()["id"])

    items = (await client.get("/api/v1/projects")).json()["items"]
    catchall_id = items[0]["id"]

    created_proj = await client.post(
        "/api/v1/projects",
        json={"title": "Other workspace", "kind": "COVERAGE"},
    )
    assert created_proj.status_code == 201
    project_b_id = created_proj.json()["id"]

    canvas_a = await client.get(f"/api/v1/projects/{catchall_id}/canvas")
    canvas_a_id = canvas_a.json()["id"]

    chat_b = await client.post(f"/api/v1/projects/{project_b_id}/chats", json={"title": "B-chat"})
    chat_b_id = UUID(chat_b.json()["id"])

    turn_repo = ChatTurnRepository(db_session)
    turn_b = await turn_repo.create(
        ChatTurn(
            chat_id=chat_b_id,
            user_id=user_id,
            turn_index=0,
            role=ChatTurnRole.USER.value,
            status=ChatTurnStatus.COMPLETED.value,
            content_markdown="external turn",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )

    bad = await client.post(
        f"/api/v1/canvases/{canvas_a_id}/elements/from-turn",
        json={
            "chatTurnId": str(turn_b.id),
            "elementType": "TEXT",
            "x": 1.0,
            "y": 2.0,
        },
    )
    assert bad.status_code == 400
    assert bad.json()["errorCode"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_post_from_source_restricts_element_types(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cel-src-type@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    me = await client.get("/api/v1/me")
    user_id = UUID(me.json()["id"])

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    canvas = await client.get(f"/api/v1/projects/{project_id}/canvas")
    canvas_id = canvas.json()["id"]

    src = Source(
        user_id=user_id,
        source_type="ARTICLE_URL",
        source_access_method="SERVER_FETCH",
        source_access_status="FULL_TEXT_EXTRACTED",
        original_input="https://example.com/a",
        normalized_url="https://example.com/a",
        canonical_url="https://example.com/a",
        file_key=None,
        file_name=None,
        mime_type=None,
        file_size_bytes=None,
        title="Example",
        publisher="Pub",
        author=None,
        published_at=None,
        extracted_text=None,
        extracted_text_word_count=None,
        extraction_confidence=None,
        extraction_error=None,
        raw_text_retention="NOT_STORED",
        content_hash=None,
        metadata_={},
        source_complexity=None,
        segment_count=None,
        scan_status=None,
    )
    db_session.add(src)
    await db_session.commit()
    await db_session.refresh(src)

    denied = await client.post(
        f"/api/v1/canvases/{canvas_id}/elements/from-source",
        json={
            "sourceId": str(src.id),
            "elementType": "AI_BLOCK",
            "contentMarkdown": "not allowed for from-source",
            "x": 0.0,
            "y": 0.0,
        },
    )
    assert denied.status_code == 400
    assert denied.json()["errorCode"] == "INVALID_INPUT"

    ok = await client.post(
        f"/api/v1/canvases/{canvas_id}/elements/from-source",
        json={
            "sourceId": str(src.id),
            "elementType": "QUOTE",
            "contentMarkdown": "short quote",
            "x": 1.0,
            "y": 2.0,
            "width": 50.0,
            "height": 40.0,
        },
    )
    assert ok.status_code == 201
    assert ok.json()["elementType"] == "QUOTE"


@pytest.mark.asyncio
async def test_patch_partial_update_and_delete(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cel-patch@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    canvas_id = (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]

    created = await client.post(
        f"/api/v1/canvases/{canvas_id}/elements",
        json={
            "elementType": "CLAIM",
            "title": "Original title",
            "contentMarkdown": "Original body text.",
            "contentJson": {"k": "v"},
            "x": 1.0,
            "y": 2.0,
            "width": 100.0,
            "height": 80.0,
            "styleJson": {},
            "provenanceKind": "MANUAL",
        },
    )
    assert created.status_code == 201
    el_id = created.json()["id"]

    patched = await client.patch(
        f"/api/v1/canvas-elements/{el_id}",
        json={
            "x": 999.0,
            "contentMarkdown": "Replaced markdown content here.",
            "archived": True,
        },
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["title"] == "Original title"
    assert body["x"] == 999.0
    assert body["contentMarkdown"] == "Replaced markdown content here."
    assert body["contentJson"] == {"k": "v"}
    assert body["archivedAt"] is not None

    listed_active = await client.get(f"/api/v1/canvases/{canvas_id}/elements?includeArchived=0")
    assert listed_active.status_code == 200
    assert el_id not in {i["id"] for i in listed_active.json()["items"]}

    listed_all = await client.get(f"/api/v1/canvases/{canvas_id}/elements?includeArchived=1")
    assert listed_all.status_code == 200
    archived_row = next(i for i in listed_all.json()["items"] if i["id"] == el_id)
    assert archived_row["archivedAt"] is not None

    deleted = await client.delete(f"/api/v1/canvas-elements/{el_id}")
    assert deleted.status_code == 204

    after = await client.get(f"/api/v1/canvases/{canvas_id}/elements?includeArchived=1")
    assert el_id not in {i["id"] for i in after.json()["items"]}


@pytest.mark.asyncio
async def test_include_archived_surfaces_archived_elements(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cel-arch@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    canvas_id = (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]

    created = await client.post(
        f"/api/v1/canvases/{canvas_id}/elements",
        json={
            "elementType": "TEXT",
            "contentMarkdown": "visible",
            "contentJson": {},
            "x": 0.0,
            "y": 0.0,
            "provenanceKind": "MANUAL",
        },
    )
    assert created.status_code == 201
    el_id = created.json()["id"]

    await client.patch(f"/api/v1/canvas-elements/{el_id}", json={"archived": True})

    hidden = await client.get(f"/api/v1/canvases/{canvas_id}/elements")
    assert el_id not in {i["id"] for i in hidden.json()["items"]}

    shown = await client.get(f"/api/v1/canvases/{canvas_id}/elements?includeArchived=1")
    assert el_id in {i["id"] for i in shown.json()["items"]}
