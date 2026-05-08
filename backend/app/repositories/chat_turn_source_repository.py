from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_turn_source import ChatTurnSource


class ChatTurnSourceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def attach(self, *, chat_turn_id: UUID, source_id: UUID) -> ChatTurnSource:
        row = ChatTurnSource(chat_turn_id=chat_turn_id, source_id=source_id)
        self._db.add(row)
        await self._db.commit()
        return row

    async def list_for_turn(self, *, chat_turn_id: UUID) -> list[ChatTurnSource]:
        stmt: Select[tuple[ChatTurnSource]] = select(ChatTurnSource).where(ChatTurnSource.chat_turn_id == chat_turn_id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def delete_for_turn(self, *, chat_turn_id: UUID) -> None:
        await self._db.execute(delete(ChatTurnSource).where(ChatTurnSource.chat_turn_id == chat_turn_id))
        await self._db.commit()

