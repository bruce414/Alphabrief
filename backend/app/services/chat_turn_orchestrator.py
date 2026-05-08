from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Callable
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_provider_client import MockAiProviderClient
from app.core.enums import ChatTurnRole, ChatTurnStatus
from app.db.session import async_session_factory
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.project import Project
from app.models.source import Source
from app.models.chat_turn_source import ChatTurnSource
from app.services.candidate_extraction_service import (
    extract_candidates_for_turn_in_session_safe,
    extract_candidates_for_turn_safe,
)
from app.services.chat_prompt_builder import build_chat_prompt
from app.services.chat_validation_service import validate_chat_reply

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AsyncSession]


async def generate_assistant_turn(
    asst_turn_id: UUID,
    *,
    session_factory: SessionFactory = async_session_factory,
) -> None:
    async with session_factory() as db:
        try:
            await _execute(asst_turn_id=asst_turn_id, db=db, session_factory=session_factory)
        except Exception:
            logger.exception("Assistant generation failed; marking FAILED (best effort)")
            async with session_factory() as db2:
                await _mark_failed(asst_turn_id=asst_turn_id, db=db2, error_code="INTERNAL")


async def _execute(*, asst_turn_id: UUID, db: AsyncSession, session_factory: SessionFactory) -> None:
    result = await db.execute(
        select(ChatTurn).where(ChatTurn.id == asst_turn_id).with_for_update()
    )
    asst = result.scalar_one_or_none()
    if asst is None:
        return
    if asst.role != ChatTurnRole.ASSISTANT.value:
        return
    if asst.status != ChatTurnStatus.QUEUED.value:
        return

    asst.status = ChatTurnStatus.RUNNING.value
    await db.commit()
    await db.refresh(asst)

    # Load chat + project.
    chat = (await db.execute(select(Chat).where(Chat.id == asst.chat_id))).scalar_one()
    project = (await db.execute(select(Project).where(Project.id == chat.project_id))).scalar_one()

    # Load prior turns (including current user turn; exclude queued assistant itself).
    prior_turns = list(
        (
            await db.execute(
                select(ChatTurn)
                .where(ChatTurn.chat_id == chat.id, ChatTurn.turn_index <= asst.turn_index)
                .order_by(ChatTurn.turn_index.asc(), ChatTurn.created_at.asc())
            )
        )
        .scalars()
        .all()
    )

    # Sources are attached to the user turn (previous index).
    user_turn = (await db.execute(
        select(ChatTurn).where(
            ChatTurn.chat_id == chat.id,
            ChatTurn.turn_index == asst.turn_index - 1,
            ChatTurn.role == ChatTurnRole.USER.value,
        )
    )).scalar_one_or_none()

    sources: list[Source] = []
    source_ids: list[UUID] = []
    if user_turn is not None:
        rows = list(
            (
                await db.execute(
                    select(ChatTurnSource).where(ChatTurnSource.chat_turn_id == user_turn.id)
                )
            )
            .scalars()
            .all()
        )
        source_ids = [r.source_id for r in rows]
        if source_ids:
            sources = list(
                (
                    await db.execute(select(Source).where(Source.id.in_(source_ids)))
                )
                .scalars()
                .all()
            )

    prompt = build_chat_prompt(chat=chat, project=project, prior_turns=prior_turns, sources=sources)
    ai = MockAiProviderClient()
    reply = await ai.generate_chat_reply(prompt)

    validation = validate_chat_reply(content_markdown=reply["content_markdown"], attached_sources=sources)

    asst.content_markdown = validation.content_markdown
    asst.content_json = reply["content_json"]
    asst.input_tokens = reply["input_tokens"]
    asst.output_tokens = reply["output_tokens"]
    asst.model_provider = "mock"
    asst.model_name = "mock"

    # Attach the same sourceIds to assistant turn.
    for sid in source_ids:
        db.add(ChatTurnSource(chat_turn_id=asst.id, source_id=sid))

    asst.status = ChatTurnStatus.COMPLETED.value
    await db.commit()

    # PHASE 2 — candidate extraction. Best-effort. Failure must NOT change the assistant turn.
    try:
        # In tests, background jobs run on a connection-bound session; avoid concurrent sessions on the same connection.
        if isinstance(db.bind, AsyncConnection):
            await extract_candidates_for_turn_in_session_safe(asst.id, db=db)
        else:
            asyncio.create_task(extract_candidates_for_turn_safe(asst.id, session_factory=session_factory))
    except Exception:
        logger.exception("Failed to schedule candidate extraction for %s", asst.id)
        # swallow — assistant reply is already saved.


async def _mark_failed(*, asst_turn_id: UUID, db: AsyncSession, error_code: str) -> None:
    result = await db.execute(select(ChatTurn).where(ChatTurn.id == asst_turn_id))
    turn = result.scalar_one_or_none()
    if turn is None:
        return
    if turn.role != ChatTurnRole.ASSISTANT.value:
        return
    if turn.status == ChatTurnStatus.COMPLETED.value:
        return
    turn.status = ChatTurnStatus.FAILED.value
    turn.error_code = error_code
    turn.error_message = "Assistant generation failed"
    await db.commit()


async def sweep_orphaned_turns(*, session_factory: SessionFactory = async_session_factory) -> None:
    async with session_factory() as db:
        await sweep_orphaned_turns_in_session(db=db)


async def sweep_orphaned_turns_in_session(*, db: AsyncSession) -> None:
    cutoff = datetime.now(UTC) - timedelta(minutes=10)
    await db.execute(
        update(ChatTurn)
        .where(
            ChatTurn.role == ChatTurnRole.ASSISTANT.value,
            ChatTurn.status == ChatTurnStatus.RUNNING.value,
            ChatTurn.updated_at < cutoff,
        )
        .values(status=ChatTurnStatus.FAILED.value, error_code="RUN_ORPHANED")
    )
    await db.commit()

