from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.chat_turn import ChatTurn


class ChatTurnRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, turn: ChatTurn) -> ChatTurn:
        self._db.add(turn)
        await self._db.commit()
        await self._db.refresh(turn)
        return turn

    async def refresh(self, turn: ChatTurn) -> ChatTurn:
        await self._db.refresh(turn)
        return turn

    async def get_by_id(self, turn_id: UUID) -> ChatTurn | None:
        result = await self._db.execute(select(ChatTurn).where(ChatTurn.id == turn_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, *, turn_id: UUID, user_id: UUID) -> ChatTurn | None:
        stmt: Select[tuple[ChatTurn]] = select(ChatTurn).where(ChatTurn.id == turn_id, ChatTurn.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_via_chat_owner(self, *, turn_id: UUID, user_id: UUID) -> ChatTurn | None:
        stmt: Select[tuple[ChatTurn]] = (
            select(ChatTurn)
            .join(Chat, Chat.id == ChatTurn.chat_id)
            .where(ChatTurn.id == turn_id, Chat.user_id == user_id)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_chat(self, *, chat_id: UUID) -> list[ChatTurn]:
        stmt: Select[tuple[ChatTurn]] = (
            select(ChatTurn).where(ChatTurn.chat_id == chat_id).order_by(asc(ChatTurn.turn_index), asc(ChatTurn.created_at))
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

