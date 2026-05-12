from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urldefrag
from uuid import UUID

import httpx
from fastapi import BackgroundTasks, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker

from app.core.enums import ChatStatus, ChatTurnRole, ChatTurnStatus, ResearchMode
from app.core.errors import AppError
from app.db.session import async_session_factory
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.chat_turn_source import ChatTurnSource
from app.models.source import Source
from app.models.user import User
from app.repositories.source_repository import SourceRepository
from app.schemas.source import CreateSourceRequest
from app.services.chat_turn_orchestrator import generate_assistant_turn, SessionFactory
from app.services.input_detection_service import detect_input
from app.services.source_service import create_source_from_request


def _make_background_session_factory_from_bind(db: AsyncSession) -> SessionFactory:
    bind = db.bind
    if isinstance(bind, AsyncEngine):
        return async_session_factory
    # In tests, `db.bind` may be a connection-bound session; create a fresh session on the same AsyncConnection
    # so BackgroundTasks can see committed rows within the test transaction.
    if isinstance(bind, AsyncConnection):
        maker = async_sessionmaker(
            bind=bind,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        def _factory() -> AsyncSession:
            return maker()

        return _factory

    return async_session_factory


def _url_lookup_candidates(raw: str) -> list[str]:
    u = raw.strip()
    base = urldefrag(u)[0].strip()
    return list(dict.fromkeys([u, base, base.rstrip("/")]))


async def send_chat_message(
    *,
    db: AsyncSession,
    current_user: User,
    chat_id: UUID,
    content: str,
    source_ids: list[UUID] | None,
    background_tasks: BackgroundTasks,
    http_client: httpx.AsyncClient,
    research_mode: ResearchMode | None = None,
    session_factory: SessionFactory | None = None,
) -> tuple[UUID, UUID, str, str, str, list[UUID]]:
    chat = (
        await db.execute(select(Chat).where(Chat.id == chat_id))
    ).scalar_one_or_none()
    if chat is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Chat not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if chat.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this chat",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if chat.status == ChatStatus.ARCHIVED.value:
        raise AppError(
            error_code="CHAT_ARCHIVED",
            message="Chat is archived",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    cleaned = (content or "").strip()
    if not cleaned:
        raise AppError(
            error_code="INVALID_INPUT",
            message="Invalid input",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    detected = detect_input(cleaned)

    explicit_ids = list(dict.fromkeys(source_ids or []))

    src_repo = SourceRepository(db)
    auto_sources: list[Source] = []
    created_source_ids: list[UUID] = []

    for url in detected.urls:
        existing = await src_repo.find_by_user_project_and_original_input_candidates(
            user_id=current_user.id,
            project_id=chat.project_id,
            candidates=_url_lookup_candidates(url),
        )
        if existing is not None:
            auto_sources.append(existing)
            continue
        created = await create_source_from_request(
            db=db,
            current_user=current_user,
            data=CreateSourceRequest(
                sourceType="AUTO_DETECT",
                input=url,
                projectId=chat.project_id,
            ),
            http_client=http_client,
        )
        created_source_ids.append(created.id)
        auto_sources.append(created)

    merged_ids: list[UUID] = []
    seen: set[UUID] = set()
    for sid in explicit_ids:
        if sid not in seen:
            merged_ids.append(sid)
            seen.add(sid)
    for src in auto_sources:
        if src.id not in seen:
            merged_ids.append(src.id)
            seen.add(src.id)

    sources_ordered: list[Source] = []
    if merged_ids:
        result = await db.execute(
            select(Source).where(Source.id.in_(merged_ids), Source.user_id == current_user.id)
        )
        rows = list(result.scalars().all())
        if len(rows) != len(merged_ids):
            raise AppError(
                error_code="INVALID_SOURCE_REF",
                message="One or more sources are unavailable.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        allowed = {"FULL_TEXT_EXTRACTED", "METADATA_ONLY"}
        if any(s.source_access_status not in allowed for s in rows):
            raise AppError(
                error_code="INVALID_SOURCE_REF",
                message="One or more sources are unavailable.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        by_id = {s.id: s for s in rows}
        sources_ordered = [by_id[mid] for mid in merged_ids]

    # Compute next user turn index.
    max_idx = (
        await db.execute(select(func.max(ChatTurn.turn_index)).where(ChatTurn.chat_id == chat.id))
    ).scalar_one()
    next_user_index = int(max_idx) + 1 if max_idx is not None else 0
    asst_index = next_user_index + 1

    now = datetime.now(UTC)

    intent_val = detected.intent_type.value
    detected_type_val = detected.primary_input_type.value

    effective_mode = research_mode or ResearchMode.STANDARD
    user_turn_content_json: dict = {"researchMode": effective_mode.value}

    user_turn = ChatTurn(
        chat_id=chat.id,
        user_id=current_user.id,
        turn_index=next_user_index,
        role=ChatTurnRole.USER.value,
        status=ChatTurnStatus.COMPLETED.value,
        content_markdown=cleaned,
        content_json=user_turn_content_json,
        model_provider=None,
        model_name=None,
        intent_type=intent_val,
        detected_input_type=detected_type_val,
    )
    asst_turn = ChatTurn(
        chat_id=chat.id,
        user_id=current_user.id,
        turn_index=asst_index,
        role=ChatTurnRole.ASSISTANT.value,
        status=ChatTurnStatus.QUEUED.value,
        content_markdown=None,
        content_json=None,
        model_provider=None,
        model_name=None,
        intent_type=intent_val,
        detected_input_type=detected_type_val,
    )

    db.add(user_turn)
    db.add(asst_turn)
    await db.flush()

    for src in sources_ordered:
        db.add(ChatTurnSource(chat_turn_id=user_turn.id, source_id=src.id))

    chat.last_turn_at = now
    if chat.title == "New chat" and next_user_index == 0:
        chat.title = cleaned[:60]

    await db.commit()

    # Fresh background session: default to app-level session factory.
    sf = session_factory or _make_background_session_factory_from_bind(db)
    background_tasks.add_task(generate_assistant_turn, asst_turn.id, session_factory=sf)

    return (
        user_turn.id,
        asst_turn.id,
        ChatTurnStatus.QUEUED.value,
        detected_type_val,
        intent_val,
        created_source_ids,
    )


async def stop_assistant_generation(
    *,
    db: AsyncSession,
    current_user: User,
    assistant_turn_id: UUID,
) -> ChatTurn:
    """Mark a generating assistant turn as failed so the user can move on."""
    result = await db.execute(
        select(ChatTurn)
        .where(ChatTurn.id == assistant_turn_id)
        .with_for_update(),
    )
    turn = result.scalar_one_or_none()
    if turn is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Chat turn not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if turn.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this chat turn",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if turn.role != ChatTurnRole.ASSISTANT.value:
        raise AppError(
            error_code="INVALID_INPUT",
            message="Only assistant replies can be stopped.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if turn.status not in (ChatTurnStatus.QUEUED.value, ChatTurnStatus.RUNNING.value):
        raise AppError(
            error_code="INVALID_INPUT",
            message="This reply is not generating.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    turn.status = ChatTurnStatus.FAILED.value
    turn.error_code = "USER_STOPPED"
    turn.error_message = "Generation stopped by user."
    await db.commit()
    await db.refresh(turn)
    return turn


async def regenerate_assistant_turn(
    *,
    db: AsyncSession,
    current_user: User,
    assistant_turn_id: UUID,
    background_tasks: BackgroundTasks,
    session_factory: SessionFactory | None = None,
) -> ChatTurn:
    """Re-queue assistant generation for the same user turn (new model reply)."""
    result = await db.execute(
        select(ChatTurn)
        .where(ChatTurn.id == assistant_turn_id)
        .with_for_update(),
    )
    turn = result.scalar_one_or_none()
    if turn is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Chat turn not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if turn.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this chat turn",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if turn.role != ChatTurnRole.ASSISTANT.value:
        raise AppError(
            error_code="INVALID_INPUT",
            message="Only assistant replies can be regenerated.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if turn.status not in (ChatTurnStatus.COMPLETED.value, ChatTurnStatus.FAILED.value):
        raise AppError(
            error_code="INVALID_INPUT",
            message="Wait for the current reply to finish, or stop it first.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user_turn = (
        await db.execute(
            select(ChatTurn).where(
                ChatTurn.chat_id == turn.chat_id,
                ChatTurn.turn_index == turn.turn_index - 1,
                ChatTurn.role == ChatTurnRole.USER.value,
            )
        )
    ).scalar_one_or_none()
    if user_turn is None:
        raise AppError(
            error_code="INVALID_INPUT",
            message="Cannot regenerate without the paired user message.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    await db.execute(delete(ChatTurnSource).where(ChatTurnSource.chat_turn_id == turn.id))

    turn.status = ChatTurnStatus.QUEUED.value
    turn.content_markdown = None
    turn.content_json = None
    turn.error_code = None
    turn.error_message = None
    turn.input_tokens = None
    turn.output_tokens = None
    turn.cache_read_tokens = None
    turn.cache_write_tokens = None
    turn.model_provider = None
    turn.model_name = None

    await db.commit()
    await db.refresh(turn)

    sf = session_factory or _make_background_session_factory_from_bind(db)
    background_tasks.add_task(generate_assistant_turn, turn.id, session_factory=sf)
    return turn
