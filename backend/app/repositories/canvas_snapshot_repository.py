from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canvas_snapshot import CanvasSnapshot


class CanvasSnapshotRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, snapshot: CanvasSnapshot) -> CanvasSnapshot:
        self._db.add(snapshot)
        await self._db.commit()
        await self._db.refresh(snapshot)
        return snapshot

    async def get_by_id(self, snapshot_id: UUID) -> CanvasSnapshot | None:
        result = await self._db.execute(select(CanvasSnapshot).where(CanvasSnapshot.id == snapshot_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, *, snapshot_id: UUID, user_id: UUID) -> CanvasSnapshot | None:
        stmt: Select[tuple[CanvasSnapshot]] = select(CanvasSnapshot).where(
            CanvasSnapshot.id == snapshot_id,
            CanvasSnapshot.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

