from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brief import Brief


class BriefRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, brief: Brief) -> Brief:
        self._db.add(brief)
        await self._db.commit()
        await self._db.refresh(brief)
        return brief

    async def update(self, brief: Brief) -> Brief:
        self._db.add(brief)
        await self._db.commit()
        await self._db.refresh(brief)
        return brief

    async def get_by_id(self, brief_id: UUID) -> Brief | None:
        result = await self._db.execute(select(Brief).where(Brief.id == brief_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, *, brief_id: UUID, user_id: UUID) -> Brief | None:
        stmt: Select[tuple[Brief]] = select(Brief).where(Brief.id == brief_id, Brief.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

