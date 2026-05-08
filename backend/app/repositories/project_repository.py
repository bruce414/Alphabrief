from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, project: Project) -> Project:
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def update(self, project: Project) -> Project:
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self._db.delete(project)
        await self._db.commit()

    async def get_by_id(self, project_id: UUID) -> Project | None:
        result = await self._db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, *, project_id: UUID, user_id: UUID) -> Project | None:
        stmt: Select[tuple[Project]] = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_catchall_for_user(self, *, user_id: UUID) -> Project | None:
        stmt: Select[tuple[Project]] = select(Project).where(Project.user_id == user_id, Project.kind == "CATCHALL")
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, *, user_id: UUID) -> list[Project]:
        stmt: Select[tuple[Project]] = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.updated_at.desc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def hard_delete_catchall_for_user(self, *, user_id: UUID) -> None:
        # Test helper convenience (not used by API).
        await self._db.execute(delete(Project).where(Project.user_id == user_id, Project.kind == "CATCHALL"))
        await self._db.commit()

