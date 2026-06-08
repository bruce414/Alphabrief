from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canvas import Canvas


class CanvasRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_for_project(self, project_id: UUID) -> Canvas | None:
        stmt: Select[tuple[Canvas]] = select(Canvas).where(Canvas.project_id == project_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_for_project(self, *, project_id: UUID, user_id: UUID) -> Canvas:
        canvas = Canvas(project_id=project_id, user_id=user_id)
        self._db.add(canvas)
        await self._db.commit()
        await self._db.refresh(canvas)
        return canvas
