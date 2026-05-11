from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_memory import ProjectMemory


class ProjectMemoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_for_project(self, project_id: UUID) -> ProjectMemory | None:
        stmt: Select[tuple[ProjectMemory]] = select(ProjectMemory).where(ProjectMemory.project_id == project_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_for_project(self, *, project_id: UUID, user_id: UUID) -> ProjectMemory:
        memory = ProjectMemory(project_id=project_id, user_id=user_id)
        self._db.add(memory)
        await self._db.commit()
        await self._db.refresh(memory)
        return memory

    async def update(self, memory: ProjectMemory) -> ProjectMemory:
        self._db.add(memory)
        await self._db.commit()
        await self._db.refresh(memory)
        return memory
