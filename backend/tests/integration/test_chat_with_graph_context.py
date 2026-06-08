"""Integration tests for graph-as-context in chat prompts."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clients.ai_provider_client import ChatPrompt, MockAiProviderClient
from app.core.enums import CanvasElementType, ProvenanceKind
from app.models.canvas_element import CanvasElement
from app.services.chat_turn_orchestrator import generate_assistant_turn


class _CapturingAiClient(MockAiProviderClient):
    def __init__(self) -> None:
        super().__init__()
        self.last_prompt: ChatPrompt | None = None

    async def generate_chat_reply(self, prompt: ChatPrompt, **kwargs: Any) -> dict[str, Any]:
        self.last_prompt = prompt
        return await super().generate_chat_reply(prompt, **kwargs)


async def _register(client, email: str) -> tuple[UUID, UUID, UUID]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert reg.status_code == 201
    me = await client.get("/api/v1/me")
    user_id = UUID(me.json()["id"])
    project_id = UUID((await client.get("/api/v1/projects")).json()["items"][0]["id"])
    canvas_id = UUID(
        (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]
    )
    return user_id, project_id, canvas_id


def _element(
    *,
    canvas_id: UUID,
    project_id: UUID,
    user_id: UUID,
    element_type: str,
    title: str,
    content_markdown: str,
) -> CanvasElement:
    return CanvasElement(
        canvas_id=canvas_id,
        project_id=project_id,
        user_id=user_id,
        element_type=element_type,
        title=title,
        content_markdown=content_markdown,
        content_json={},
        x=Decimal("100"),
        y=Decimal("100"),
        width=Decimal("200"),
        height=Decimal("120"),
        z_index=0,
        style_json=None,
        provenance_kind=ProvenanceKind.MANUAL.value,
        provenance_chat_turn_id=None,
        provenance_source_id=None,
        confidence_label=None,
        archived_at=None,
    )


@pytest.mark.asyncio
async def test_chat_prompt_includes_graph_context_and_response_count(
    client,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capturing = _CapturingAiClient()
    monkeypatch.setattr(
        "app.services.chat_turn_orchestrator.get_ai_provider_client",
        lambda: capturing,
    )

    user_id, project_id, canvas_id = await _register(client, "graphctx@example.com")
    db_session.add(
        _element(
            canvas_id=canvas_id,
            project_id=project_id,
            user_id=user_id,
            element_type=CanvasElementType.DIRECTION.value,
            title="Semiconductor cycle",
            content_markdown="Track memory pricing and capex.",
        )
    )
    db_session.add(
        _element(
            canvas_id=canvas_id,
            project_id=project_id,
            user_id=user_id,
            element_type=CanvasElementType.RISK.value,
            title="Memory glut risk",
            content_markdown="Oversupply could pressure memory pricing.",
        )
    )
    db_session.add(
        _element(
            canvas_id=canvas_id,
            project_id=project_id,
            user_id=user_id,
            element_type=CanvasElementType.CLAIM.value,
            title="Pricing power claim",
            content_markdown="Leaders retain pricing power in memory.",
        )
    )
    await db_session.commit()

    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "Graph chat"})
    chat_id = UUID(chat.json()["id"])

    sent = await client.post(
        f"/api/v1/chats/{chat_id}/turns",
        json={"content": "Which memory pricing risk has the weakest evidence?"},
    )
    assert sent.status_code == 200
    payload = sent.json()
    assert payload["graphContextNodeCount"] == 3

    asst_id = UUID(payload["assistantTurnId"])
    bind = db_session.bind
    assert bind is not None
    session_factory = async_sessionmaker(
        bind=bind,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    await generate_assistant_turn(asst_id, session_factory=session_factory)

    assert capturing.last_prompt is not None
    system = capturing.last_prompt.system
    assert "## Your research graph context" in system
    assert "**Center:** Semiconductor cycle" in system
    assert "[RISK] Memory glut risk" in system

    got = await client.get(f"/api/v1/chat-turns/{asst_id}")
    assert got.json()["status"] == "COMPLETED"
