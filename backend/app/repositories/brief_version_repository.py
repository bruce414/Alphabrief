from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brief_version import BriefVersion


class BriefVersionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, version: BriefVersion) -> BriefVersion:
        self._db.add(version)
        await self._db.commit()
        await self._db.refresh(version)
        return version

    async def update(self, version: BriefVersion) -> BriefVersion:
        self._db.add(version)
        await self._db.commit()
        await self._db.refresh(version)
        return version

    async def get_by_id(self, version_id: UUID) -> BriefVersion | None:
        result = await self._db.execute(select(BriefVersion).where(BriefVersion.id == version_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, *, version_id: UUID, user_id: UUID) -> BriefVersion | None:
        stmt: Select[tuple[BriefVersion]] = select(BriefVersion).where(
            BriefVersion.id == version_id,
            BriefVersion.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

