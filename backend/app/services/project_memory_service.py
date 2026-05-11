from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemoryUpdatedBy
from app.core.errors import AppError
from app.models.project_memory import ProjectMemory
from app.repositories.project_memory_repository import ProjectMemoryRepository
from app.repositories.project_repository import ProjectRepository


class ProjectMemoryService:
    def __init__(
        self,
        *,
        db: AsyncSession,
        repo: ProjectMemoryRepository,
        project_repo: ProjectRepository,
    ) -> None:
        self._db = db
        self._repo = repo
        self._project_repo = project_repo

    async def _get_project_owned(self, *, user_id: UUID, project_id: UUID) -> None:
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

    def _normalize_new_memory(self, memory: ProjectMemory) -> ProjectMemory:
        """Ensure lazy-created rows match DATA_MODEL empty-array defaults."""
        memory.entities_json = []
        memory.themes_json = []
        memory.open_questions_json = []
        memory.conclusions_json = []
        memory.updated_by = MemoryUpdatedBy.SYSTEM.value
        return memory

    async def get_or_create(self, *, user_id: UUID, project_id: UUID) -> ProjectMemory:
        await self._get_project_owned(user_id=user_id, project_id=project_id)

        existing = await self._repo.get_for_project(project_id)
        if existing is not None:
            return existing

        created = await self._repo.create_for_project(project_id=project_id, user_id=user_id)
        normalized = self._normalize_new_memory(created)
        return await self._repo.update(normalized)

    async def patch(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        summary_markdown: str | None = None,
        entities: list[Any] | None = None,
        themes: list[Any] | None = None,
        open_questions: list[Any] | None = None,
        conclusions: list[Any] | None = None,
    ) -> ProjectMemory:
        memory = await self.get_or_create(user_id=user_id, project_id=project_id)

        changed = False

        if summary_markdown is not None:
            memory.summary_markdown = summary_markdown
            changed = True

        if entities is not None:
            if not isinstance(entities, list):
                raise AppError(
                    error_code="INVALID_INPUT",
                    message="Invalid input",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            memory.entities_json = entities
            changed = True

        if themes is not None:
            if not isinstance(themes, list):
                raise AppError(
                    error_code="INVALID_INPUT",
                    message="Invalid input",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            memory.themes_json = themes
            changed = True

        if open_questions is not None:
            if not isinstance(open_questions, list):
                raise AppError(
                    error_code="INVALID_INPUT",
                    message="Invalid input",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            memory.open_questions_json = open_questions
            changed = True

        if conclusions is not None:
            if not isinstance(conclusions, list):
                raise AppError(
                    error_code="INVALID_INPUT",
                    message="Invalid input",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            memory.conclusions_json = conclusions
            changed = True

        if changed:
            memory.updated_by = MemoryUpdatedBy.USER.value
            return await self._repo.update(memory)

        return memory

    async def refresh_from_activity(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        max_activity_items: int = 30,
    ) -> dict[str, Any]:
        await self._get_project_owned(user_id=user_id, project_id=project_id)
        _ = max_activity_items  # reserved for AI refresh (API_SPEC §13)
        # TODO: Wired in later milestone — see AI_PIPELINE §11 (AI-backed memory refresh).
        return {"memoryRefreshJobId": None, "status": "NOT_IMPLEMENTED"}
