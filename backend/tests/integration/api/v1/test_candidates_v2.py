"""Integration tests for candidate_elements list / promote / dismiss (v0.3 Canvas flow)."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.core.enums import CandidateStatus, CanvasElementType
from app.models.candidate_element import CandidateElement
from app.models.chat_turn import ChatTurn
from app.repositories.chat_turn_repository import ChatTurnRepository


@pytest.mark.asyncio
async def test_get_candidates_lists_pending_only_by_default(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "candv2-list@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    me = await client.get("/api/v1/me")
    user_id = UUID(me.json()["id"])

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "c"})
    chat_id = UUID(chat.json()["id"])

    repo = ChatTurnRepository(db_session)
    turn = await repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=0,
            role="USER",
            status="COMPLETED",
            content_markdown="turn",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )

    pending = CandidateElement(
        chat_turn_id=turn.id,
        project_id=UUID(project_id),
        user_id=user_id,
        suggested_element_type=CanvasElementType.CLAIM.value,
        title="P",
        content_markdown="pending body",
        content_json={},
        status=CandidateStatus.PENDING.value,
        promoted_element_id=None,
        extraction_model_name=None,
    )
    promoted = CandidateElement(
        chat_turn_id=turn.id,
        project_id=UUID(project_id),
        user_id=user_id,
        suggested_element_type=CanvasElementType.CLAIM.value,
        title="Done",
        content_markdown="done body",
        content_json={},
        status=CandidateStatus.PROMOTED.value,
        promoted_element_id=None,
        extraction_model_name=None,
    )
    db_session.add(pending)
    db_session.add(promoted)
    await db_session.commit()
    await db_session.refresh(pending)
    await db_session.refresh(promoted)

    resp = await client.get(f"/api/v1/chat-turns/{turn.id}/candidates")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(pending.id)
    assert items[0]["suggestedElementType"] == "CLAIM"
    assert items[0]["status"] == "PENDING"

    all_resp = await client.get(f"/api/v1/chat-turns/{turn.id}/candidates?includeAll=1")
    assert len(all_resp.json()["items"]) == 2


@pytest.mark.asyncio
async def test_promote_creates_element_idempotent_and_dismiss_flow(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "candv2-promo@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    me = await client.get("/api/v1/me")
    user_id = UUID(me.json()["id"])

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    canvas_id = (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]

    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "c"})
    chat_id = UUID(chat.json()["id"])

    repo = ChatTurnRepository(db_session)
    turn = await repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=0,
            role="USER",
            status="COMPLETED",
            content_markdown="src",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )

    cand = CandidateElement(
        chat_turn_id=turn.id,
        project_id=UUID(project_id),
        user_id=user_id,
        suggested_element_type=CanvasElementType.CLAIM.value,
        title="T",
        content_markdown="candidate markdown",
        content_json={"hint": 1},
        status=CandidateStatus.PENDING.value,
        promoted_element_id=None,
        extraction_model_name=None,
    )
    db_session.add(cand)
    await db_session.commit()
    await db_session.refresh(cand)

    promote_body = {
        "canvasId": canvas_id,
        "elementType": "CLAIM",
        "x": 12.0,
        "y": 34.0,
        "width": 200.0,
        "height": 100.0,
    }

    p1 = await client.post(f"/api/v1/candidates/{cand.id}/promote", json=promote_body)
    assert p1.status_code == 201
    elem = p1.json()
    assert elem["provenanceKind"] == "CANDIDATE"
    assert elem["provenanceChatTurnId"] == str(turn.id)
    assert elem["contentMarkdown"] == "candidate markdown"
    eid = elem["id"]

    p2 = await client.post(f"/api/v1/candidates/{cand.id}/promote", json=promote_body)
    assert p2.status_code == 201
    assert p2.json()["id"] == eid

    dismiss_other = CandidateElement(
        chat_turn_id=turn.id,
        project_id=UUID(project_id),
        user_id=user_id,
        suggested_element_type=CanvasElementType.TEXT.value,
        title=None,
        content_markdown="to dismiss",
        content_json={},
        status=CandidateStatus.PENDING.value,
        promoted_element_id=None,
        extraction_model_name=None,
    )
    db_session.add(dismiss_other)
    await db_session.commit()
    await db_session.refresh(dismiss_other)

    d1 = await client.post(f"/api/v1/candidates/{dismiss_other.id}/dismiss")
    assert d1.status_code == 200
    d2 = await client.post(f"/api/v1/candidates/{dismiss_other.id}/dismiss")
    assert d2.status_code == 200

    bad = await client.post(
        f"/api/v1/candidates/{dismiss_other.id}/promote",
        json=promote_body,
    )
    assert bad.status_code == 400
    assert bad.json()["errorCode"] == "CANDIDATE_DISMISSED"


@pytest.mark.asyncio
async def test_cross_user_cannot_promote_candidate_returns_403(client, db_session):
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "candv2-own@example.com", "password": "password123"},
    )
    assert reg1.status_code == 201

    me = await client.get("/api/v1/me")
    user_id = UUID(me.json()["id"])

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    canvas_id = (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]

    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "c"})
    chat_id = UUID(chat.json()["id"])

    repo = ChatTurnRepository(db_session)
    turn = await repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=0,
            role="USER",
            status="COMPLETED",
            content_markdown="x",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )

    cand = CandidateElement(
        chat_turn_id=turn.id,
        project_id=UUID(project_id),
        user_id=user_id,
        suggested_element_type=CanvasElementType.TEXT.value,
        title=None,
        content_markdown="body",
        content_json={},
        status=CandidateStatus.PENDING.value,
        promoted_element_id=None,
        extraction_model_name=None,
    )
    db_session.add(cand)
    await db_session.commit()
    await db_session.refresh(cand)

    await client.post("/api/v1/auth/logout")

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "candv2-other@example.com", "password": "password123"},
    )
    assert reg2.status_code == 201

    denied = await client.post(
        f"/api/v1/candidates/{cand.id}/promote",
        json={
            "canvasId": canvas_id,
            "elementType": "TEXT",
            "x": 1.0,
            "y": 2.0,
        },
    )
    assert denied.status_code == 403
    assert denied.json()["errorCode"] == "FORBIDDEN"
