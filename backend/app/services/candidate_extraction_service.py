from __future__ import annotations

import logging
from typing import Callable
from uuid import UUID

import bleach
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_provider_client import AiProviderClient, MockAiProviderClient
from app.core.enums import CandidateStatus, CanvasBlockType
from app.db.session import async_session_factory
from app.models.candidate_block import CandidateBlock
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.chat_turn_source import ChatTurnSource
from app.models.project import Project
from app.models.source import Source
from app.models.usage_event import UsageEvent


logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AsyncSession]


ALLOWED_TAGS = [
    "p",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "h2",
    "h3",
    "code",
    "blockquote",
    "a",
]


async def extract_candidates_for_turn_safe(
    asst_turn_id: UUID,
    *,
    session_factory: SessionFactory = async_session_factory,
    ai_provider: AiProviderClient | None = None,
) -> None:
    """Top-level Phase 2 entry. Never raises."""
    try:
        async with session_factory() as db:
            # Tests run everything inside a connection-scoped nested transaction.
            # Opening a second session on the same connection must create its own savepoint.
            await db.begin_nested()
            await _extract(asst_turn_id=asst_turn_id, db=db, ai_provider=ai_provider)
    except Exception:
        logger.exception("Candidate extraction failed for %s; skipping.", asst_turn_id)


async def extract_candidates_for_turn_in_session_safe(
    asst_turn_id: UUID,
    *,
    db: AsyncSession,
    ai_provider: AiProviderClient | None = None,
) -> None:
    """Best-effort extraction using an existing session. Never raises."""
    try:
        await _extract(asst_turn_id=asst_turn_id, db=db, ai_provider=ai_provider)
    except Exception:
        logger.exception("Candidate extraction failed for %s; skipping.", asst_turn_id)


async def _extract(*, asst_turn_id: UUID, db: AsyncSession, ai_provider: AiProviderClient | None) -> None:
    # Load assistant turn.
    asst = (await db.execute(select(ChatTurn).where(ChatTurn.id == asst_turn_id))).scalar_one_or_none()
    if asst is None:
        return
    if not (asst.content_markdown or "").strip():
        return

    # Load chat + project.
    chat = (await db.execute(select(Chat).where(Chat.id == asst.chat_id))).scalar_one()
    project = (await db.execute(select(Project).where(Project.id == chat.project_id))).scalar_one()
    _ = project  # soft-mode for CATCHALL: we still run extraction

    # Load user message: previous user turn in the same chat.
    user_turn = (
        await db.execute(
            select(ChatTurn).where(
                ChatTurn.chat_id == asst.chat_id,
                ChatTurn.turn_index == asst.turn_index - 1,
            )
        )
    ).scalar_one_or_none()
    user_message = (user_turn.content_markdown if user_turn is not None else "") or ""

    # Load attached sources from user turn.
    sources: list[Source] = []
    if user_turn is not None:
        rows = list(
            (
                await db.execute(select(ChatTurnSource).where(ChatTurnSource.chat_turn_id == user_turn.id))
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

    ai = ai_provider or MockAiProviderClient()
    extracted = await ai.extract_candidates(
        user_message=user_message,
        assistant_reply=asst.content_markdown or "",
        attached_sources=sources,
    )

    created_count = 0
    for c in extracted:
        block_type_raw = (c.get("block_type") or "").strip()
        content_raw = (c.get("content_markdown") or "").strip()
        title_raw = c.get("title")
        title = title_raw.strip()[:500] if isinstance(title_raw, str) and title_raw.strip() else None

        if not content_raw:
            continue
        try:
            block_type = CanvasBlockType(block_type_raw)
        except Exception:
            continue

        cleaned = bleach.clean(
            content_raw,
            tags=ALLOWED_TAGS,
            attributes={"a": ["href", "title"]},
            strip=True,
        ).strip()
        if not cleaned:
            continue

        db.add(
            CandidateBlock(
                chat_turn_id=asst.id,
                project_id=chat.project_id,
                user_id=asst.user_id,
                block_type=block_type.value,
                title=title,
                content_markdown=cleaned,
                status=CandidateStatus.PENDING.value,
                promoted_block_id=None,
                extraction_model_name=getattr(asst, "model_name", None),
            )
        )
        created_count += 1

    # Best-effort usage record (old UsageEvent schema).
    if created_count > 0:
        db.add(
            UsageEvent(
                user_id=asst.user_id,
                source_id=None,
                event_type="CANDIDATE_EXTRACTION",
                model_provider=asst.model_provider,
                model_name=asst.model_name,
                input_tokens=None,
                output_tokens=None,
                estimated_allowance_impact_percent=None,
                actual_allowance_impact_percent=None,
                internal_cost_score=None,
                estimated_cost_usd=None,
            )
        )

    await db.commit()

