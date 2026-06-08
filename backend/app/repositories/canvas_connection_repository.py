from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canvas_connection import CanvasConnection


class CanvasConnectionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, connection: CanvasConnection, *, commit: bool = True) -> CanvasConnection:
        self._db.add(connection)
        if commit:
            await self._db.commit()
        else:
            await self._db.flush()
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

    async def list_for_project_between_elements(
        self,
        *,
        project_id: UUID,
        element_ids: set[UUID],
    ) -> list[CanvasConnection]:
        if not element_ids:
            return []
        stmt: Select[tuple[CanvasConnection]] = (
            select(CanvasConnection)
            .where(
                CanvasConnection.project_id == project_id,
                CanvasConnection.from_element_id.in_(element_ids),
                CanvasConnection.to_element_id.in_(element_ids),
            )
            .order_by(CanvasConnection.created_at.asc(), CanvasConnection.id.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
