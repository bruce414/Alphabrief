from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, chat: Chat) -> Chat:
        self._db.add(chat)
        await self._db.commit()
        await self._db.refresh(chat)
        return chat

    async def update(self, chat: Chat) -> Chat:
        self._db.add(chat)
        await self._db.commit()
        await self._db.refresh(chat)
        return chat

    async def delete(self, chat: Chat) -> None:
        await self._db.delete(chat)
        await self._db.commit()

    async def get_by_id(self, chat_id: UUID) -> Chat | None:
        result = await self._db.execute(select(Chat).where(Chat.id == chat_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, *, chat_id: UUID, user_id: UUID) -> Chat | None:
        stmt: Select[tuple[Chat]] = select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_project(
        self,
        *,
        project_id: UUID,
        include_archived: bool,
        limit: int,
        cursor_chat: Chat | None,
    ) -> list[Chat]:
        stmt: Select[tuple[Chat]] = select(Chat).where(Chat.project_id == project_id)
        if not include_archived:
            stmt = stmt.where(Chat.status != "ARCHIVED")

        if cursor_chat is not None:
            cursor_last: datetime | None = cursor_chat.last_turn_at
            cursor_created = cursor_chat.created_at
            cursor_id = cursor_chat.id

            if cursor_last is None:
                stmt = stmt.where(
                    and_(
                        Chat.last_turn_at.is_(None),
                        or_(
                            Chat.created_at < cursor_created,
                            and_(Chat.created_at == cursor_created, Chat.id < cursor_id),
                        ),
                    )
                )
            else:
                stmt = stmt.where(
                    or_(
                        Chat.last_turn_at.is_(None),
                        Chat.last_turn_at < cursor_last,
                        and_(
                            Chat.last_turn_at == cursor_last,
                            or_(
                                Chat.created_at < cursor_created,
                                and_(Chat.created_at == cursor_created, Chat.id < cursor_id),
                            ),
                        ),
                    )
                )

        stmt = (
            stmt.order_by(
                Chat.last_turn_at.desc().nullslast(),
                Chat.created_at.desc(),
                Chat.id.desc(),
            )
            .limit(limit)
        )

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def hard_delete_for_project(self, *, project_id: UUID) -> None:
        # Test helper convenience (not used by API).
        await self._db.execute(delete(Chat).where(Chat.project_id == project_id))
        await self._db.commit()

