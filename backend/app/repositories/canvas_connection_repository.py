from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canvas_connection import CanvasConnection


class CanvasConnectionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, connection: CanvasConnection) -> CanvasConnection:
        self._db.add(connection)
        await self._db.commit()
        await self._db.refresh(connection)
        return connection

    async def update(self, connection: CanvasConnection) -> CanvasConnection:
        self._db.add(connection)
        await self._db.commit()
        await self._db.refresh(connection)
        return connection

    async def delete(self, connection: CanvasConnection) -> None:
        await self._db.delete(connection)
        await self._db.commit()

    async def get_by_id(self, conn_id: UUID) -> CanvasConnection | None:
        result = await self._db.execute(select(CanvasConnection).where(CanvasConnection.id == conn_id))
        return result.scalar_one_or_none()

    async def list_for_canvas(self, *, canvas_id: UUID) -> list[CanvasConnection]:
        stmt: Select[tuple[CanvasConnection]] = (
            select(CanvasConnection)
            .where(CanvasConnection.canvas_id == canvas_id)
            .order_by(CanvasConnection.created_at.asc(), CanvasConnection.id.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
