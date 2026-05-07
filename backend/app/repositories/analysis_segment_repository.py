from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_segment import AnalysisSegment


class AnalysisSegmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, segment: AnalysisSegment) -> AnalysisSegment:
        self._db.add(segment)
        await self._db.flush()
        return segment

    async def list_by_run_id(self, run_id: UUID) -> list[AnalysisSegment]:
        result = await self._db.execute(
            select(AnalysisSegment)
            .where(AnalysisSegment.analysis_run_id == run_id)
            .order_by(AnalysisSegment.segment_index.asc())
        )
        return list(result.scalars().all())

