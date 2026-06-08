from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canvas_element import CanvasElement


class CanvasElementRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, element: CanvasElement, *, commit: bool = True) -> CanvasElement:
        self._db.add(element)
        if commit:
            await self._db.commit()
        else:
            await self._db.flush()
        await self._db.refresh(element)
        return element

    async def update(self, element: CanvasElement) -> CanvasElement:
        self._db.add(element)
        await self._db.commit()
        await self._db.refresh(element)
        return element

    async def delete(self, element: CanvasElement) -> None:
        await self._db.delete(element)
        await self._db.commit()

    async def get_by_id(self, element_id: UUID) -> CanvasElement | None:
        result = await self._db.execute(select(CanvasElement).where(CanvasElement.id == element_id))
        return result.scalar_one_or_none()

    async def list_for_canvas(
        self,
        *,
        canvas_id: UUID,
        include_archived: bool,
    ) -> list[CanvasElement]:
        stmt: Select[tuple[CanvasElement]] = select(CanvasElement).where(CanvasElement.canvas_id == canvas_id)
        if not include_archived:
            stmt = stmt.where(CanvasElement.archived_at.is_(None))
        stmt = stmt.order_by(
            CanvasElement.z_index.asc(),
            CanvasElement.created_at.asc(),
            CanvasElement.id.asc(),
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_non_archived_for_project(self, *, project_id: UUID) -> list[CanvasElement]:
        stmt: Select[tuple[CanvasElement]] = (
            select(CanvasElement)
            .where(
                CanvasElement.project_id == project_id,
                CanvasElement.archived_at.is_(None),
            )
            .order_by(
                CanvasElement.updated_at.desc(),
                CanvasElement.created_at.asc(),
                CanvasElement.id.asc(),
            )
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
