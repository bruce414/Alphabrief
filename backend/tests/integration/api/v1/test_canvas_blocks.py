from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.canvas_block import CanvasBlock
from app.models.source import Source


def _dec(pos_str: str) -> Decimal:
    return Decimal(pos_str)


@pytest.mark.asyncio
async def test_post_manual_appends_to_end_with_position_gt_existing(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb1@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    b1 = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "one"},
    )
    assert b1.status_code == 201
    b2 = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "two"},
    )
    assert b2.status_code == 201

    b3 = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "three"},
    )
    assert b3.status_code == 201

    p1 = _dec(b1.json()["positionIndex"])
    p2 = _dec(b2.json()["positionIndex"])
    p3 = _dec(b3.json()["positionIndex"])
    assert p3 > max(p1, p2)


@pytest.mark.asyncio
async def test_post_from_turn_sets_provenance_and_defaults_content(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb2@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "T"})
    assert chat.status_code == 201
    chat_id = chat.json()["id"]

    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Hello canvas"})
    assert sent.status_code == 200
    user_turn_id = sent.json()["userTurnId"]

    promoted = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks/from-turn",
        json={"chatTurnId": user_turn_id, "blockType": "SUMMARY"},
    )
    assert promoted.status_code == 201
    body = promoted.json()
    assert body["provenanceKind"] == "CHAT_TURN"
    assert body["provenanceChatTurnId"] == user_turn_id
    assert body["contentMarkdown"] == "Hello canvas"


@pytest.mark.asyncio
async def test_post_from_source_sets_provenance_source_id(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb3@example.com", "password": "password123"},
    )
    assert reg.status_code == 201
    me = await client.get("/api/v1/me")
    user_id = me.json()["id"]

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    src = Source(
        user_id=UUID(user_id),
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
        publisher="ExamplePub",
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

    created = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks/from-source",
        json={
            "sourceId": str(src.id),
            "blockType": "QUOTE",
            "contentMarkdown": "Short quote",
        },
    )
    assert created.status_code == 201
    assert created.json()["provenanceKind"] == "SOURCE"
    assert created.json()["provenanceSourceId"] == str(src.id)


@pytest.mark.asyncio
async def test_post_with_position_after_inserts_between_neighbors(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb4@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    b1 = (await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "A"},
    )).json()
    b2 = (await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "B"},
    )).json()
    b3 = (await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "C"},
    )).json()

    inserted = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "X", "positionAfter": b2["id"]},
    )
    assert inserted.status_code == 201

    listed = await client.get(f"/api/v1/projects/{project_id}/canvas-blocks")
    assert listed.status_code == 200
    items = listed.json()["items"]
    contents = [i["contentMarkdown"] for i in items]
    assert contents == ["A", "B", "X", "C"]

    p_b = next(_dec(i["positionIndex"]) for i in items if i["contentMarkdown"] == "B")
    p_x = next(_dec(i["positionIndex"]) for i in items if i["contentMarkdown"] == "X")
    p_c = next(_dec(i["positionIndex"]) for i in items if i["contentMarkdown"] == "C")
    assert p_b < p_x < p_c


@pytest.mark.asyncio
async def test_rebalance_trigger_after_many_inserts_between_1_and_2(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb5@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    first = (await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "first"},
    )).json()
    _second = (await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "second"},
    )).json()

    for i in range(50):
        r = await client.post(
            f"/api/v1/projects/{project_id}/canvas-blocks",
            json={
                "blockType": "NOTE",
                "contentMarkdown": f"mid-{i}",
                "positionAfter": first["id"],
            },
        )
        assert r.status_code == 201

    listed = await client.get(f"/api/v1/projects/{project_id}/canvas-blocks")
    assert listed.status_code == 200
    items = listed.json()["items"]
    positions = [_dec(i["positionIndex"]) for i in items]
    gaps = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
    assert min(gaps) >= Decimal("1.0")


@pytest.mark.asyncio
async def test_catchall_metadata_flag_and_should_suggest_conversion(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb6@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    catchall_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    for i in range(3):
        r = await client.post(
            f"/api/v1/projects/{catchall_id}/canvas-blocks",
            json={"blockType": "NOTE", "contentMarkdown": f"n{i}"},
        )
        assert r.status_code == 201

    listed = await client.get(f"/api/v1/projects/{catchall_id}/canvas-blocks")
    assert listed.status_code == 200
    assert listed.json()["shouldSuggestProjectConversion"] is True

    rows = list(
        (
            await db_session.execute(
                select(CanvasBlock).where(CanvasBlock.project_id == UUID(catchall_id))
            )
        )
        .scalars()
        .all()
    )
    assert rows
    assert all(b.metadata_.get("from_catchall") is True for b in rows)

    # Non-catchall should not have the flag.
    created = await client.post(
        "/api/v1/projects",
        json={"title": "Real", "kind": "THESIS"},
    )
    assert created.status_code == 201
    real_id = created.json()["id"]
    r2 = await client.post(
        f"/api/v1/projects/{real_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "x"},
    )
    assert r2.status_code == 201
    bid = UUID(r2.json()["id"])
    b = (await db_session.execute(select(CanvasBlock).where(CanvasBlock.id == bid))).scalar_one()
    assert b.metadata_.get("from_catchall") is None


@pytest.mark.asyncio
async def test_cross_user_post_patch_delete_returns_403(client):
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb7-owner@example.com", "password": "password123"},
    )
    assert reg1.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    created = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "owner block"},
    )
    assert created.status_code == 201
    block_id = created.json()["id"]

    await client.post("/api/v1/auth/logout")

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb7-other@example.com", "password": "password123"},
    )
    assert reg2.status_code == 201

    post = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "hack"},
    )
    assert post.status_code == 403

    patch = await client.patch(
        f"/api/v1/canvas-blocks/{block_id}",
        json={"contentMarkdown": "hack"},
    )
    assert patch.status_code == 403

    deleted = await client.delete(f"/api/v1/canvas-blocks/{block_id}")
    assert deleted.status_code == 403


@pytest.mark.asyncio
async def test_patch_archived_hides_from_default_get(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cb8@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    created = await client.post(
        f"/api/v1/projects/{project_id}/canvas-blocks",
        json={"blockType": "NOTE", "contentMarkdown": "keep me"},
    )
    assert created.status_code == 201
    block_id = created.json()["id"]

    patched = await client.patch(f"/api/v1/canvas-blocks/{block_id}", json={"archived": True})
    assert patched.status_code == 200
    assert patched.json()["archivedAt"] is not None

    listed = await client.get(f"/api/v1/projects/{project_id}/canvas-blocks")
    assert listed.status_code == 200
    assert listed.json()["items"] == []

    listed2 = await client.get(f"/api/v1/projects/{project_id}/canvas-blocks?includeArchived=1")
    assert listed2.status_code == 200
    assert len(listed2.json()["items"]) == 1
    assert listed2.json()["items"][0]["id"] == block_id

