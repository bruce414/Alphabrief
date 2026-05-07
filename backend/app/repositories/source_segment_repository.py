from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_segment import SourceSegment


class SourceSegmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add_all(self, segments: list[SourceSegment]) -> list[SourceSegment]:
        """Stage many segments inside the caller's transaction."""

        for seg in segments:
            self._db.add(seg)
        await self._db.flush()
        return segments

    async def list_for_scan(self, scan_id: UUID) -> list[SourceSegment]:
        stmt = (
            select(SourceSegment)
            .where(SourceSegment.source_scan_id == scan_id)
            .order_by(SourceSegment.segment_index)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
