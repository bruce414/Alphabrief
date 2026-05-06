from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source


class SourceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, source: Source) -> Source:
        self._db.add(source)
        await self._db.commit()
        await self._db.refresh(source)
        return source

    async def update(self, source: Source) -> Source:
        self._db.add(source)
        await self._db.commit()
        await self._db.refresh(source)
        return source

    async def get_by_id_for_user(self, source_id: UUID, user_id: UUID) -> Source | None:
        stmt = select(Source).where(Source.id == source_id, Source.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, source_id: UUID) -> Source | None:
        stmt = select(Source).where(Source.id == source_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
