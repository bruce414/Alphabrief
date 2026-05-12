from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_provider_client import AiProviderClient, MemoryRefresh, get_ai_provider_client
from app.core.config import settings
from app.core.enums import MemoryUpdatedBy
from app.core.errors import AppError
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.project_memory import ProjectMemory
from app.models.usage_event import UsageEvent
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

    def _apply_memory_refresh(self, memory: ProjectMemory, refresh: MemoryRefresh) -> None:
        sm = refresh.get("summary_markdown")
        if isinstance(sm, str) and sm.strip():
            memory.summary_markdown = sm.strip()

        list_fields: tuple[tuple[str, str], ...] = (
            ("entities", "entities_json"),
            ("themes", "themes_json"),
            ("open_questions", "open_questions_json"),
            ("conclusions", "conclusions_json"),
        )
        for refresh_key, attr in list_fields:
            raw = refresh.get(refresh_key)  # type: ignore[arg-type]
            if isinstance(raw, list) and len(raw) > 0:
                cleaned = [str(x).strip() for x in raw if str(x).strip()]
                if cleaned:
                    setattr(memory, attr, cleaned)

    async def refresh_from_activity(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        max_activity_items: int = 30,
        ai_provider: AiProviderClient | None = None,
    ) -> dict[str, Any]:
        memory = await self.get_or_create(user_id=user_id, project_id=project_id)

        project = await self._project_repo.get_by_id(project_id)
        if project is None:  # pragma: no cover - get_or_create already validated
            raise AppError(
                error_code="NOT_FOUND",
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        stmt = (
            select(ChatTurn)
            .join(Chat, Chat.id == ChatTurn.chat_id)
            .where(Chat.project_id == project_id)
            .order_by(desc(ChatTurn.created_at))
            .limit(max_activity_items)
        )
        turns = list((await self._db.execute(stmt)).scalars().all())
        turns.reverse()

        if not turns:
            return {"memoryRefreshJobId": str(memory.id), "status": "NO_ACTIVITY"}

        recent_turns_markdown: list[str] = []
        for turn in turns:
            role = (turn.role or "USER").strip().upper()
            if role not in ("USER", "ASSISTANT"):
                role = "USER"
            body = (turn.content_markdown or "").strip()
            recent_turns_markdown.append(f"{role}\n{body}")

        current_summary = (memory.summary_markdown or "").strip()
        current_memory_summary: str | None = current_summary if current_summary else None

        ai = ai_provider or get_ai_provider_client()
        refresh = await ai.refresh_project_memory(
            project_title=project.title,
            current_memory_summary=current_memory_summary,
            recent_turns_markdown=recent_turns_markdown,
        )

        self._apply_memory_refresh(memory, refresh)
        memory.updated_by = MemoryUpdatedBy.AI.value

        self._db.add(
            UsageEvent(
                user_id=user_id,
                source_id=None,
                event_type="MEMORY_UPDATE",
                model_provider=settings.ai_provider,
                model_name=settings.anthropic_model if settings.ai_provider == "anthropic" else None,
                input_tokens=None,
                output_tokens=None,
                estimated_allowance_impact_percent=None,
                actual_allowance_impact_percent=None,
                internal_cost_score=None,
                estimated_cost_usd=None,
            )
        )
        await self._repo.update(memory)

        return {"memoryRefreshJobId": str(memory.id), "status": "COMPLETED"}
