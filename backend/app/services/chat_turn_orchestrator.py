from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.clients.ai_provider_client import ResearchEvent, get_ai_provider_client
from app.core.config import settings
from app.core.enums import ChatTurnRole, ChatTurnStatus, ResearchMode
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
from app.services.reply_tail_sections import parse_reply_tail_sections

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AsyncSession]


# Throttle DB commits while streaming events (avoid hammering the DB on chatty streams).
_EVENT_FLUSH_INTERVAL_SECONDS = 0.6


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


def _parse_research_mode(value: Any) -> ResearchMode:
    if isinstance(value, ResearchMode):
        return value
    if isinstance(value, str):
        try:
            return ResearchMode(value.upper())
        except ValueError:
            return ResearchMode.STANDARD
    return ResearchMode.STANDARD


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
    asst.content_json = {"events": [], "webSearchResults": []}
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

    # research_mode is persisted on the user turn's content_json (see chat_turn_service).
    research_mode = ResearchMode.STANDARD
    if user_turn is not None and isinstance(user_turn.content_json, dict):
        research_mode = _parse_research_mode(user_turn.content_json.get("researchMode"))

    prompt = build_chat_prompt(chat=chat, project=project, prior_turns=prior_turns, sources=sources)
    ai_client = get_ai_provider_client()

    events: list[ResearchEvent] = []
    last_flush_at = 0.0
    pending_flush = False

    async def _flush_events(force: bool = False) -> None:
        nonlocal last_flush_at, pending_flush
        now_t = time.monotonic()
        if not force and (now_t - last_flush_at) < _EVENT_FLUSH_INTERVAL_SECONDS:
            return
        try:
            payload = dict(asst.content_json or {})
            payload["events"] = list(events)
            asst.content_json = payload
            flag_modified(asst, "content_json")
            await db.commit()
            last_flush_at = now_t
            pending_flush = False
        except Exception:
            logger.exception("Failed to flush research events for turn %s", asst.id)
            # Best effort; continue.

    async def on_event(event: ResearchEvent) -> None:
        nonlocal pending_flush
        # Coalesce "search running" → "search done" by replacing trailing pending search
        # of the same id when a "done" arrives without a query (we only have one running at a time).
        if event.get("type") == "search" and event.get("status") == "done":
            for i in range(len(events) - 1, -1, -1):
                ev = events[i]
                if ev.get("type") == "search" and ev.get("status") == "running":
                    merged = {**ev, **event}
                    events[i] = merged
                    break
            else:
                events.append(event)
        else:
            events.append(event)
        pending_flush = True
        await _flush_events(force=False)

    try:
        reply = await ai_client.generate_chat_reply(
            prompt,
            research_mode=research_mode,
            on_event=on_event,
        )
    finally:
        if pending_flush:
            await _flush_events(force=True)

    await db.refresh(asst)
    if asst.status != ChatTurnStatus.RUNNING.value:
        logger.info(
            "Skipping assistant completion for turn %s (status=%s); likely user-stopped.",
            asst.id,
            asst.status,
        )
        return

    main_md, mentioned_entities, suggested_canvas_insights, follow_up_questions = (
        parse_reply_tail_sections(reply["content_markdown"])
    )
    validation = validate_chat_reply(content_markdown=main_md, attached_sources=sources)

    web_search_results = reply.get("web_search_results") or []

    # Persist web search results into web sources (METADATA_ONLY) and attach to assistant turn.
    web_source_ids: list[UUID] = []
    if web_search_results and user_turn is not None:
        web_source_ids = await _persist_web_search_sources(
            db=db,
            user_id=asst.user_id,
            project_id=chat.project_id,
            results=web_search_results,
        )

    # Build merged content_json: keep events log, add provider/model + web search results.
    merged_content_json: dict[str, Any] = {
        **(reply.get("content_json") or {}),
        "events": list(events),
        "webSearchResults": web_search_results,
        "followUpQuestions": follow_up_questions,
        "mentionedEntities": mentioned_entities,
        "suggestedCanvasInsights": suggested_canvas_insights,
    }
    asst.content_markdown = validation.content_markdown
    asst.content_json = merged_content_json
    asst.input_tokens = reply["input_tokens"]
    asst.output_tokens = reply["output_tokens"]
    asst.model_provider = settings.ai_provider
    asst.model_name = settings.anthropic_model if settings.ai_provider == "anthropic" else "mock"

    # Attach user-provided sources AND any web search sources to the assistant turn.
    already_attached: set[UUID] = set()
    for sid in source_ids:
        if sid not in already_attached:
            db.add(ChatTurnSource(chat_turn_id=asst.id, source_id=sid))
            already_attached.add(sid)
    for sid in web_source_ids:
        if sid not in already_attached:
            db.add(ChatTurnSource(chat_turn_id=asst.id, source_id=sid))
            already_attached.add(sid)

    asst.status = ChatTurnStatus.COMPLETED.value
    await db.commit()

    # Auto-generate a smart chat title once, after the first assistant reply completes.
    await _maybe_generate_title(
        db=db,
        ai_client=ai_client,
        chat=chat,
        user_message=(user_turn.content_markdown if user_turn else "") or "",
        assistant_reply=validation.content_markdown,
        first_turn=(asst.turn_index == 1),
    )

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


async def _persist_web_search_sources(
    *,
    db: AsyncSession,
    user_id: UUID,
    project_id: UUID | None,
    results: list[dict[str, Any]],
) -> list[UUID]:
    """Persist deduped web-search results as METADATA_ONLY sources scoped to the user/project.

    Reuses an existing source if (user, project, normalized_url) already matches.
    """
    from app.repositories.source_repository import SourceRepository

    out_ids: list[UUID] = []
    seen_urls: set[str] = set()
    repo = SourceRepository(db)

    for entry in results:
        url = (entry.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        title = entry.get("title") or None
        publisher = entry.get("publisher") or None

        existing = await repo.find_by_user_project_and_original_input_candidates(
            user_id=user_id,
            project_id=project_id,
            candidates=[url],
        )
        if existing is not None:
            out_ids.append(existing.id)
            continue

        src = Source(
            user_id=user_id,
            project_id=project_id,
            source_type="ARTICLE_URL",
            source_access_method="WEB_SEARCH",
            source_access_status="METADATA_ONLY",
            original_input=url,
            normalized_url=url,
            canonical_url=url,
            title=title,
            publisher=publisher,
            raw_text_retention="NONE",
            metadata_={"origin": "ai_web_search"},
        )
        db.add(src)
        await db.flush()
        out_ids.append(src.id)

    return out_ids


async def _maybe_generate_title(
    *,
    db: AsyncSession,
    ai_client,
    chat: Chat,
    user_message: str,
    assistant_reply: str,
    first_turn: bool,
) -> None:
    if not first_turn:
        return
    meta = dict(chat.metadata_ or {})
    if meta.get("auto_title_generated"):
        return
    try:
        title = await ai_client.generate_chat_title(
            user_message=user_message,
            assistant_reply=assistant_reply,
        )
    except Exception:
        logger.warning("Chat title generation failed; leaving existing title", exc_info=True)
        return

    title = (title or "").strip()
    if not title:
        return

    chat.title = title[:80]
    meta["auto_title_generated"] = True
    chat.metadata_ = meta
    flag_modified(chat, "metadata_")
    await db.commit()


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
