"""Integration tests for tightened candidate extraction (v0.3)."""

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
    ProvenanceKind,
)
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

    async def generate_chat_reply(self, prompt):  # pragma: no cover - unused
        raise NotImplementedError

    async def extract_candidates(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        attached_sources,
    ) -> list[dict[str, Any]]:
        return list(self._items)


async def _seed_assistant_turn(
    *,
    client,
    db_session,
    email: str,
) -> tuple[UUID, UUID, UUID]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert reg.status_code == 201

    me = await client.get("/api/v1/me")
    user_id = UUID(me.json()["id"])

    project_id = UUID((await client.get("/api/v1/projects")).json()["items"][0]["id"])
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
    return user_id, project_id, asst.id


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
async def test_extract_caps_at_two_candidates(client, db_session):
    _, _, asst_id = await _seed_assistant_turn(
        client=client, db_session=db_session, email="tight-cap@example.com"
    )

    ai = _StubAi(
        [
            {"kind": "CLAIM", "title": "C1", "body": "one"},
            {"kind": "RISK", "title": "C2", "body": "two"},
            {"kind": "EVIDENCE", "title": "C3", "body": "three"},
            {"kind": "QUESTION", "title": "C4", "body": "four"},
            {"kind": "CLAIM", "title": "C5", "body": "five"},
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = await _candidates_for_turn(db_session, asst_id)
    assert len(rows) == 2
    assert rows[0].title == "C1"
    assert rows[1].title == "C2"


@pytest.mark.asyncio
async def test_extract_drops_disallowed_kinds(client, db_session):
    _, _, asst_id = await _seed_assistant_turn(
        client=client, db_session=db_session, email="tight-kinds@example.com"
    )

    ai = _StubAi(
        [
            {"kind": "THEME", "title": "skip theme", "body": "theme body"},
            {"kind": "TEXT", "title": "skip text", "body": "text body"},
            {"kind": "CLAIM", "title": "keep", "body": "claim body"},
            {"kind": "RISK", "title": "also keep", "body": "risk body"},
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = await _candidates_for_turn(db_session, asst_id)
    assert len(rows) == 2
    kinds = {r.suggested_element_type for r in rows}
    assert kinds == {CanvasElementType.CLAIM.value, CanvasElementType.RISK.value}


@pytest.mark.asyncio
async def test_extract_dedupes_against_existing_canvas_element_titles(
    client, db_session
):
    user_id, project_id, asst_id = await _seed_assistant_turn(
        client=client,
        db_session=db_session,
        email="tight-dedup@example.com",
    )

    canvas_id = UUID(
        (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]
    )
    db_session.add(
        CanvasElement(
            canvas_id=canvas_id,
            project_id=project_id,
            user_id=user_id,
            element_type=CanvasElementType.CLAIM.value,
            title="  Existing   Claim  ",
            content_markdown="already on canvas",
            content_json={},
            x=Decimal("0"),
            y=Decimal("0"),
            width=None,
            height=None,
            z_index=0,
            style_json=None,
            provenance_kind=ProvenanceKind.MANUAL.value,
            provenance_chat_turn_id=None,
            provenance_source_id=None,
            confidence_label=None,
            archived_at=None,
        )
    )
    await db_session.commit()

    ai = _StubAi(
        [
            {
                "kind": "CLAIM",
                "title": "existing claim",
                "body": "duplicate title should drop",
            },
            {"kind": "QUESTION", "title": "Fresh gap", "body": "new question"},
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = await _candidates_for_turn(db_session, asst_id)
    assert len(rows) == 1
    assert rows[0].title == "Fresh gap"
    assert rows[0].suggested_element_type == CanvasElementType.QUESTION.value


@pytest.mark.asyncio
async def test_extract_empty_llm_response_is_ok(client, db_session):
    _, _, asst_id = await _seed_assistant_turn(
        client=client, db_session=db_session, email="tight-empty@example.com"
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=_StubAi([])
    )

    rows = await _candidates_for_turn(db_session, asst_id)
    assert rows == []
