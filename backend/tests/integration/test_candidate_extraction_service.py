"""Integration tests for candidate_extraction_service.

These cover the v0.3 contract: extraction writes rows to candidate_elements
using suggested_element_type (not the legacy block_type), persists optional
suggested_position into content_json, and stays best-effort (never raises).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.enums import (
    CandidateStatus,
    CanvasElementType,
    ChatTurnRole,
    ChatTurnStatus,
)
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
        existing_canvas_elements=None,
    ) -> list[dict[str, Any]]:
        _ = (user_message, assistant_reply, attached_sources, existing_canvas_elements)
        return list(self._items)


class _RaisingAi:
    async def generate_chat_reply(self, prompt):  # pragma: no cover - unused
        raise NotImplementedError

    async def extract_candidates(self, **_kwargs):
        raise RuntimeError("provider exploded")


async def _seed_assistant_turn(
    *,
    client,
    db_session,
    email: str,
) -> tuple[UUID, UUID, UUID]:
    """Register a user, create a chat with USER + ASSISTANT turns, return ids."""
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


@pytest.mark.asyncio
async def test_extract_writes_candidate_elements_with_suggested_element_type(
    client, db_session
):
    _, project_id, asst_id = await _seed_assistant_turn(
        client=client, db_session=db_session, email="cand-extract-1@example.com"
    )

    ai = _StubAi(
        [
            {
                "suggested_element_type": "CLAIM",
                "title": "T1",
                "content_markdown": "First candidate body.",
                "suggested_position": {"x": 10, "y": 20, "width": 300, "height": 150},
            },
            {
                "suggested_element_type": "QUESTION",
                "title": "T2",
                "content_markdown": "Why does this matter?",
            },
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = list(
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
    assert len(rows) == 2

    first = rows[0]
    assert first.suggested_element_type == CanvasElementType.CLAIM.value
    assert first.title == "T1"
    assert first.content_markdown == "First candidate body."
    assert first.status == CandidateStatus.PENDING.value
    assert first.project_id == project_id
    assert first.extraction_model_name == "mock-model"
    assert first.content_json == {
        "suggested_position": {"x": 10.0, "y": 20.0, "width": 300.0, "height": 150.0}
    }

    second = rows[1]
    assert second.suggested_element_type == CanvasElementType.QUESTION.value
    assert second.content_json == {}


@pytest.mark.asyncio
async def test_extract_skips_unknown_or_invalid_element_types(client, db_session):
    _, _, asst_id = await _seed_assistant_turn(
        client=client, db_session=db_session, email="cand-extract-2@example.com"
    )

    ai = _StubAi(
        [
            {
                "suggested_element_type": "NOT_A_TYPE",
                "title": "skip",
                "content_markdown": "body",
            },
            {
                "suggested_element_type": "CLAIM",
                "title": "ok",
                "content_markdown": "<script>x</script>kept",
            },
            {
                "suggested_element_type": "TEXT",
                "title": "empty",
                "content_markdown": "   ",
            },
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = list(
        (
            await db_session.execute(
                select(CandidateElement).where(CandidateElement.chat_turn_id == asst_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].suggested_element_type == CanvasElementType.CLAIM.value
    assert "<script>" not in rows[0].content_markdown
    assert "kept" in rows[0].content_markdown


@pytest.mark.asyncio
async def test_extract_ignores_invalid_suggested_position_payload(client, db_session):
    _, _, asst_id = await _seed_assistant_turn(
        client=client, db_session=db_session, email="cand-extract-3@example.com"
    )

    ai = _StubAi(
        [
            {
                "suggested_element_type": "CLAIM",
                "title": "bad-pos",
                "content_markdown": "ok",
                "suggested_position": "nope",
            },
            {
                "suggested_element_type": "CLAIM",
                "title": "partial-pos",
                "content_markdown": "ok2",
                "suggested_position": {"x": 1.5, "y": "bad", "width": 2},
            },
        ]
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=ai
    )

    rows = list(
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
    assert len(rows) == 2
    assert rows[0].content_json == {}
    assert rows[1].content_json == {
        "suggested_position": {"x": 1.5, "width": 2.0}
    }


@pytest.mark.asyncio
async def test_extract_never_raises_when_provider_errors(client, db_session):
    _, _, asst_id = await _seed_assistant_turn(
        client=client, db_session=db_session, email="cand-extract-4@example.com"
    )

    await extract_candidates_for_turn_in_session_safe(
        asst_id, db=db_session, ai_provider=_RaisingAi()
    )

    rows = list(
        (
            await db_session.execute(
                select(CandidateElement).where(CandidateElement.chat_turn_id == asst_id)
            )
        )
        .scalars()
        .all()
    )
    assert rows == []
