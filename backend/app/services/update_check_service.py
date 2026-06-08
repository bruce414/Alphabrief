from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository


def _now_utc() -> datetime:
    return datetime.now(UTC)


async def run_update_check(db: AsyncSession, project_id: UUID) -> Project:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if project is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Project not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    project.last_checked_at = _now_utc()
    # TODO: replace with real freshness detection in v0.4
    return await repo.update(project)
