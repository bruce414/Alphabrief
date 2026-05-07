from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis_run import AnalysisRun


class AnalysisRunRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, run: AnalysisRun) -> AnalysisRun:
        self._db.add(run)
        await self._db.flush()
        return run

    async def get_by_id(self, run_id: UUID, *, with_segments: bool = False) -> AnalysisRun | None:
        stmt = select(AnalysisRun).where(AnalysisRun.id == run_id)
        if with_segments:
            stmt = stmt.options(selectinload(AnalysisRun.segments))
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

