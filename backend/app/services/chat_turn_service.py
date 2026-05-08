from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import BackgroundTasks, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker

from app.core.enums import ChatStatus, ChatTurnRole, ChatTurnStatus
from app.core.errors import AppError
from app.db.session import async_session_factory
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.chat_turn_source import ChatTurnSource
from app.models.source import Source
from app.models.user import User
from app.services.chat_turn_orchestrator import generate_assistant_turn, SessionFactory


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


async def send_chat_message(
    *,
    db: AsyncSession,
    current_user: User,
    chat_id: UUID,
    content: str,
    source_ids: list[UUID] | None,
    background_tasks: BackgroundTasks,
    session_factory: SessionFactory | None = None,
) -> tuple[UUID, UUID, str]:
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

    source_ids = list(dict.fromkeys(source_ids or []))
    sources: list[Source] = []
    if source_ids:
        result = await db.execute(
            select(Source).where(Source.id.in_(source_ids), Source.user_id == current_user.id)
        )
        sources = list(result.scalars().all())
        if len(sources) != len(source_ids):
            raise AppError(
                error_code="INVALID_SOURCE_REF",
                message="One or more sources are unavailable.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        allowed = {"FULL_TEXT_EXTRACTED", "METADATA_ONLY"}
        if any(s.source_access_status not in allowed for s in sources):
            raise AppError(
                error_code="INVALID_SOURCE_REF",
                message="One or more sources are unavailable.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # Compute next user turn index.
    max_idx = (
        await db.execute(select(func.max(ChatTurn.turn_index)).where(ChatTurn.chat_id == chat.id))
    ).scalar_one()
    next_user_index = int(max_idx) + 1 if max_idx is not None else 0
    asst_index = next_user_index + 1

    now = datetime.now(UTC)

    user_turn = ChatTurn(
        chat_id=chat.id,
        user_id=current_user.id,
        turn_index=next_user_index,
        role=ChatTurnRole.USER.value,
        status=ChatTurnStatus.COMPLETED.value,
        content_markdown=cleaned,
        content_json=None,
        model_provider=None,
        model_name=None,
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
    )

    db.add(user_turn)
    db.add(asst_turn)
    await db.flush()

    for src in sources:
        db.add(ChatTurnSource(chat_turn_id=user_turn.id, source_id=src.id))

    chat.last_turn_at = now
    if chat.title == "New chat" and next_user_index == 0:
        chat.title = cleaned[:60]

    await db.commit()

    # Fresh background session: default to app-level session factory.
    sf = session_factory or _make_background_session_factory_from_bind(db)
    background_tasks.add_task(generate_assistant_turn, asst_turn.id, session_factory=sf)

    return user_turn.id, asst_turn.id, ChatTurnStatus.QUEUED.value

