from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
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

    async def find_by_user_project_and_original_input_candidates(
        self,
        *,
        user_id: UUID,
        project_id: UUID | None,
        candidates: list[str],
    ) -> Source | None:
        """Reuse an existing source row when the same URL string was stored."""
        uniq = list(dict.fromkeys([c for c in candidates if c]))
        if not uniq:
            return None
        stmt = (
            select(Source)
            .where(Source.user_id == user_id)
            .where(Source.project_id == project_id)
            .where(or_(*(Source.original_input == c for c in uniq)))
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
