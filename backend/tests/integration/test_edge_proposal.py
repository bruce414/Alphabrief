"""Integration tests for candidate edge proposals at extraction and promote time."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.enums import (
    CanvasElementType,
    ChatTurnRole,
    ChatTurnStatus,
    CandidateStatus,
    ProvenanceKind,
)
from app.models.canvas_connection import CanvasConnection
from app.models.canvas_element import CanvasElement
from app.models.candidate_element import CandidateElement
from app.models.chat_turn import ChatTurn
from app.repositories.chat_turn_repository import ChatTurnRepository
from app.services.candidate_extraction_service import (
    extract_candidates_for_turn_in_session_safe,
)


class _StubAi:
    def __init__(self, items: list[dict[str, Any]]) -> None:
        self._items = items

    async def extract_candidates(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        attached_sources,
        existing_canvas_elements=None,
    ) -> list[dict[str, Any]]:
        _ = (user_message, assistant_reply, attached_sources, existing_canvas_elements)
        return list(self._items)


async def _register_and_project(client, email: str) -> tuple[UUID, UUID]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert reg.status_code == 201
    me = await client.get("/api/v1/me")
    user_id = UUID(me.json()["id"])
    project_id = UUID((await client.get("/api/v1/projects")).json()["items"][0]["id"])
    return user_id, project_id


async def _seed_turn(
    *,
    client,
    db_session,
    email: str,
) -> tuple[UUID, UUID, UUID, UUID]:
    user_id, project_id = await _register_and_project(client, email)
    canvas_id = UUID(
        (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]
    )
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "c"})
    chat_id = UUID(chat.json()["id"])

    repo = ChatTurnRepository(db_session)
    await repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=0,
            role=ChatTurnRole.USER.value,
            status=ChatTurnStatus.COMPLETED.value,
            content_markdown="user message",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )
    asst = await repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=1,
            role=ChatTurnRole.ASSISTANT.value,
            status=ChatTurnStatus.COMPLETED.value,
            content_markdown="### A heading\n\nBody text.",
            content_json=None,
            model_provider="mock",
            model_name="mock-model",
        )
    )
    return user_id, project_id, canvas_id, asst.id


async def _add_direction(
    db_session,
    *,
    canvas_id: UUID,
    project_id: UUID,
    user_id: UUID,
    title: str,
) -> CanvasElement:
    direction = CanvasElement(
        canvas_id=canvas_id,
        project_id=project_id,
        user_id=user_id,
        element_type=CanvasElementType.DIRECTION.value,
        title=title,
        content_markdown="Summary",
        content_json={},
        x=Decimal("400"),
        y=Decimal("300"),
        width=Decimal("280"),
        height=Decimal("100"),
        z_index=0,
        style_json=None,
        provenance_kind=ProvenanceKind.AI_ONBOARDING.value,
        provenance_chat_turn_id=None,
        provenance_source_id=None,
        confidence_label=None,
        archived_at=None,
    )
    db_session.add(direction)
    await db_session.commit()
    await db_session.refresh(direction)
    return direction


async def _candidates_for_turn(db_session, asst_id: UUID) -> list[CandidateElement]:
    return list(
        (
            await db_session.execute(
                select(CandidateElement)
                .where(CandidateElement.chat_turn_id == asst_id)
                .order_by(CandidateElement.created_at.asc())
            )
        )
        .scalars()
        .all()
    )


@pytest.mark.asyncio
async def test_extract_resolves_proposed_edge_to_target_element_id(client, db_session):
    user_id, project_id, canvas_id, asst_id = await _seed_turn(
        client=client,
        db_session=db_session,
        email="edge-resolve@example.com",
    )
    direction = await _add_direction(
        db_session,
        canvas_id=canvas_id,
        project_id=project_id,
        user_id=user_id,
        title="AI infrastructure capex cycle",
    )

    ai = _StubAi(
        [
            {
                "kind": "CLAIM",
                "title": "Hyperscaler spend accelerates",
                "body": "Cloud capex is re-accelerating into 2026.",
                "proposed_edge": {
                    "edge_type": "supports",
                    "target_title": "AI infrastructure capex cycle",
                },
            }
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = await _candidates_for_turn(db_session, asst_id)
    assert len(rows) == 1
    proposed = rows[0].content_json.get("proposed_edge")
    assert proposed == {
        "edge_type": "supports",
        "target_element_id": str(direction.id),
        "target_title": "AI infrastructure capex cycle",
    }


@pytest.mark.asyncio
async def test_extract_drops_disallowed_edge_type_but_keeps_candidate(client, db_session):
    user_id, project_id, canvas_id, asst_id = await _seed_turn(
        client=client,
        db_session=db_session,
        email="edge-bad-type@example.com",
    )
    await _add_direction(
        db_session,
        canvas_id=canvas_id,
        project_id=project_id,
        user_id=user_id,
        title="Direction anchor",
    )

    ai = _StubAi(
        [
            {
                "kind": "RISK",
                "title": "Supply bottleneck",
                "body": "Lead times are stretching.",
                "proposed_edge": {
                    "edge_type": "causes",
                    "target_title": "Direction anchor",
                },
            }
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = await _candidates_for_turn(db_session, asst_id)
    assert len(rows) == 1
    assert "proposed_edge" not in (rows[0].content_json or {})


@pytest.mark.asyncio
async def test_extract_drops_edge_when_target_title_missing(client, db_session):
    _, _, _, asst_id = await _seed_turn(
        client=client,
        db_session=db_session,
        email="edge-missing-target@example.com",
    )

    ai = _StubAi(
        [
            {
                "kind": "QUESTION",
                "title": "Open gap",
                "body": "What breaks the thesis?",
                "proposed_edge": {
                    "edge_type": "contradicts",
                    "target_title": "Nonexistent element title",
                },
            }
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = await _candidates_for_turn(db_session, asst_id)
    assert len(rows) == 1
    assert "proposed_edge" not in (rows[0].content_json or {})


@pytest.mark.asyncio
async def test_promote_creates_element_and_connection_when_edge_resolved(client, db_session):
    user_id, project_id, canvas_id, asst_id = await _seed_turn(
        client=client,
        db_session=db_session,
        email="edge-promote@example.com",
    )
    direction = await _add_direction(
        db_session,
        canvas_id=canvas_id,
        project_id=project_id,
        user_id=user_id,
        title="Rates path and credit spreads",
    )

    cand = CandidateElement(
        chat_turn_id=asst_id,
        project_id=project_id,
        user_id=user_id,
        suggested_element_type=CanvasElementType.CLAIM.value,
        title="IG spreads compress",
        content_markdown="Spreads tightened after the policy pivot.",
        content_json={
            "proposed_edge": {
                "edge_type": "affects",
                "target_element_id": str(direction.id),
            }
        },
        status=CandidateStatus.PENDING.value,
        promoted_element_id=None,
        extraction_model_name=None,
    )
    db_session.add(cand)
    await db_session.commit()
    await db_session.refresh(cand)

    promote_body = {
        "canvasId": str(canvas_id),
        "elementType": "CLAIM",
        "x": 120.0,
        "y": 220.0,
        "width": 200.0,
        "height": 110.0,
    }
    resp = await client.post(f"/api/v1/candidates/{cand.id}/promote", json=promote_body)
    assert resp.status_code == 201, resp.text
    new_element_id = UUID(resp.json()["id"])

    connections = list(
        (
            await db_session.execute(
                select(CanvasConnection).where(CanvasConnection.canvas_id == canvas_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(connections) == 1
    conn = connections[0]
    assert conn.from_element_id == new_element_id
    assert conn.to_element_id == direction.id
    assert conn.connection_type == "affects"
    assert conn.label is None


@pytest.mark.asyncio
async def test_promote_without_proposed_edge_creates_no_connection(client, db_session):
    user_id, project_id, canvas_id, asst_id = await _seed_turn(
        client=client,
        db_session=db_session,
        email="edge-promote-none@example.com",
    )

    cand = CandidateElement(
        chat_turn_id=asst_id,
        project_id=project_id,
        user_id=user_id,
        suggested_element_type=CanvasElementType.QUESTION.value,
        title="What changes conviction?",
        content_markdown="Need a catalyst to revisit sizing.",
        content_json={},
        status=CandidateStatus.PENDING.value,
        promoted_element_id=None,
        extraction_model_name=None,
    )
    db_session.add(cand)
    await db_session.commit()
    await db_session.refresh(cand)

    resp = await client.post(
        f"/api/v1/candidates/{cand.id}/promote",
        json={
            "canvasId": str(canvas_id),
            "elementType": "QUESTION",
            "x": 80.0,
            "y": 160.0,
            "width": 200.0,
            "height": 110.0,
        },
    )
    assert resp.status_code == 201

    count = (
        await db_session.execute(
            select(CanvasConnection).where(CanvasConnection.canvas_id == canvas_id)
        )
    ).scalars().all()
    assert count == []
