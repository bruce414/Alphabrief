from __future__ import annotations

from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.canvas import Canvas
from app.repositories.canvas_repository import CanvasRepository
from app.repositories.project_repository import ProjectRepository


class CanvasService:
    def __init__(
        self,
        *,
        db: AsyncSession,
        canvas_repo: CanvasRepository,
        project_repo: ProjectRepository,
    ) -> None:
        self._db = db
        self._canvas_repo = canvas_repo
        self._project_repo = project_repo

    async def get_or_create_for_project(self, *, user_id: UUID, project_id: UUID) -> Canvas:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise AppError(
                error_code="NOT_FOUND",
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if project.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this project",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        existing = await self._canvas_repo.get_for_project(project_id)
        if existing is not None:
            return existing

        return await self._canvas_repo.create_for_project(project_id=project_id, user_id=user_id)
