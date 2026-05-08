from __future__ import annotations

from datetime import UTC, datetime

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ProjectKind
from app.core.errors import AppError
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository


def _now_utc() -> datetime:
    return datetime.now(UTC)


class ProjectService:
    def __init__(self, repo: ProjectRepository) -> None:
        self._repo = repo

    async def ensure_catchall_for_user(self, *, user: User, db: AsyncSession) -> Project:
        """Idempotent. Returns existing catchall or creates one."""
        existing = await self._repo.get_catchall_for_user(user_id=user.id)
        if existing is not None:
            return existing

        project = Project(
            user_id=user.id,
            kind=ProjectKind.CATCHALL.value,
            title="__catchall__",
            description=None,
            archived_at=None,
            metadata_={},
        )

        try:
            return await self._repo.create(project)
        except IntegrityError:
            # Race: another request created it after our read.
            await db.rollback()
            existing2 = await self._repo.get_catchall_for_user(user_id=user.id)
            if existing2 is None:
                raise
            return existing2

    async def create_project(
        self,
        *,
        user: User,
        title: str,
        kind: ProjectKind,
        description: str | None,
    ) -> Project:
        if kind == ProjectKind.CATCHALL:
            raise AppError(
                error_code="INVALID_PROJECT_KIND",
                message="CATCHALL projects cannot be created by users",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        project = Project(
            user_id=user.id,
            kind=kind.value,
            title=title,
            description=description,
            archived_at=None,
            metadata_={},
        )
        return await self._repo.create(project)

    async def list_projects_for_user(self, *, user: User, db: AsyncSession) -> list[Project]:
        projects = await self._repo.list_for_user(user_id=user.id)

        catchall = next((p for p in projects if p.kind == ProjectKind.CATCHALL.value), None)
        if catchall is None:
            # Legacy user: lazily ensure catchall.
            catchall = await self.ensure_catchall_for_user(user=user, db=db)
            projects = await self._repo.list_for_user(user_id=user.id)

        # Catchall first; remaining by updated_at desc (repo already orders desc).
        ordered: list[Project] = []
        for p in projects:
            if p.kind == ProjectKind.CATCHALL.value:
                continue
            ordered.append(p)
        return [catchall, *ordered]

    async def get_project_or_forbidden(self, *, user: User, project_id) -> Project:
        project = await self._repo.get_by_id(project_id)
        if project is None:
            raise AppError(
                error_code="NOT_FOUND",
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if project.user_id != user.id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this project",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return project

    async def patch_project(
        self,
        *,
        user: User,
        project_id,
        title: str | None,
        description: str | None,
        archived: bool | None,
    ) -> Project:
        project = await self.get_project_or_forbidden(user=user, project_id=project_id)
        if project.kind == ProjectKind.CATCHALL.value:
            raise AppError(
                error_code="IMMUTABLE_CATCHALL",
                message="Catchall project is immutable",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if title is not None:
            project.title = title
        if description is not None:
            project.description = description
        if archived is not None:
            project.archived_at = _now_utc() if archived else None
        return await self._repo.update(project)

    async def delete_project(self, *, user: User, project_id) -> None:
        project = await self.get_project_or_forbidden(user=user, project_id=project_id)
        if project.kind == ProjectKind.CATCHALL.value:
            raise AppError(
                error_code="IMMUTABLE_CATCHALL",
                message="Catchall project is immutable",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        await self._repo.delete(project)

