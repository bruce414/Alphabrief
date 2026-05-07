from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.source_scan import SourceScan


class SourceScanRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, scan: SourceScan) -> SourceScan:
        """Stage a new scan row inside the caller's transaction."""

        self._db.add(scan)
        await self._db.flush()
        return scan

    async def get_by_id(self, scan_id: UUID) -> SourceScan | None:
        stmt = (
            select(SourceScan)
            .options(selectinload(SourceScan.segments))
            .where(SourceScan.id == scan_id)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
