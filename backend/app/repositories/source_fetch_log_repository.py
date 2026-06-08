from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_fetch_log import SourceFetchLog


class SourceFetchLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, row: SourceFetchLog) -> SourceFetchLog:
        self._db.add(row)
        await self._db.commit()
        await self._db.refresh(row)
        return row

