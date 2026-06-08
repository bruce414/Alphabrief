from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypedDict
from uuid import UUID

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ChatStatus, ProjectKind
from app.core.errors import AppError
from app.models.brief import Brief
from app.models.canvas import Canvas
from app.models.canvas_element import CanvasElement
from app.models.chat import Chat
from app.models.project import Project
from app.models.source import Source
from app.models.user import User
from app.repositories.canvas_repository import CanvasRepository
from app.repositories.project_memory_repository import ProjectMemoryRepository
from app.repositories.project_repository import ProjectRepository
from app.services.canvas_service import CanvasService
from app.services.project_memory_service import ProjectMemoryService


def _now_utc() -> datetime:
    return datetime.now(UTC)


class OverviewPatchFields(TypedDict, total=False):
    research_goal: str | None
    research_type: str | None
    included_topics: list[str] | None
    excluded_topics: list[str] | None
    target_entities: list[str] | None
    time_horizon: str | None


@dataclass(frozen=True)
class ProjectCounts:
    chat_count: int
    canvas_element_count: int
    source_count: int
    brief_count: int


@dataclass(frozen=True)
class ProjectWithCounts:
    project: Project
    counts: ProjectCounts


class ProjectService:
    def __init__(self, repo: ProjectRepository) -> None:
        self._repo = repo

    async def _provision_canvas_and_memory(self, *, db: AsyncSession, user_id: UUID, project_id: UUID) -> None:
        canvas_repo = CanvasRepository(db)
        memory_repo = ProjectMemoryRepository(db)
        canvas_svc = CanvasService(db=db, canvas_repo=canvas_repo, project_repo=self._repo)
        memory_svc = ProjectMemoryService(db=db, repo=memory_repo, project_repo=self._repo)
        await canvas_svc.get_or_create_for_project(user_id=user_id, project_id=project_id)
        await memory_svc.get_or_create(user_id=user_id, project_id=project_id)

    async def _counts_for_project_ids(self, db: AsyncSession, project_ids: list[UUID]) -> dict[UUID, ProjectCounts]:
        if not project_ids:
            return {}

        chat_sq = (
            select(func.count(Chat.id))
            .where(
                Chat.project_id == Project.id,
                Chat.status != ChatStatus.ARCHIVED.value,
            )
            .scalar_subquery()
        )

        canvas_el_sq = (
            select(func.count(CanvasElement.id))
            .select_from(CanvasElement)
            .join(Canvas, CanvasElement.canvas_id == Canvas.id)
            .where(
                Canvas.project_id == Project.id,
                CanvasElement.archived_at.is_(None),
            )
            .scalar_subquery()
        )

        source_sq = (
            select(func.count(Source.id))
            .where(Source.project_id == Project.id)
            .scalar_subquery()
        )

        brief_sq = (
            select(func.count(Brief.id))
            .where(Brief.project_id == Project.id)
            .scalar_subquery()
        )

        stmt = (
            select(
                Project.id,
                chat_sq.label("chat_count"),
                canvas_el_sq.label("canvas_element_count"),
                source_sq.label("source_count"),
                brief_sq.label("brief_count"),
            ).where(Project.id.in_(project_ids))
        )

        result = await db.execute(stmt)
        out: dict[UUID, ProjectCounts] = {}
        for row in result.mappings():
            pid = row["id"]
            out[pid] = ProjectCounts(
                chat_count=int(row["chat_count"]),
                canvas_element_count=int(row["canvas_element_count"]),
                source_count=int(row["source_count"]),
                brief_count=int(row["brief_count"]),
            )
        return out

    async def ensure_canvas_and_memory_for_project(
        self,
        *,
        user: User,
        project_id: UUID,
        db: AsyncSession,
    ) -> None:
        await self._provision_canvas_and_memory(db=db, user_id=user.id, project_id=project_id)

    async def counts_for_single_project(
        self,
        *,
        db: AsyncSession,
        project_id: UUID,
    ) -> ProjectCounts:
        m = await self._counts_for_project_ids(db, [project_id])
        return m[project_id]

    async def ensure_catchall_for_user(self, *, user: User, db: AsyncSession) -> Project:
        """Idempotent. Returns existing catchall or creates one."""
        existing = await self._repo.get_catchall_for_user(user_id=user.id)
        if existing is not None:
            await self._provision_canvas_and_memory(db=db, user_id=user.id, project_id=existing.id)
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
            created = await self._repo.create(project)
            await self._provision_canvas_and_memory(db=db, user_id=user.id, project_id=created.id)
            return created
        except IntegrityError:
            # Race: another request created it after our read.
            await db.rollback()
            existing2 = await self._repo.get_catchall_for_user(user_id=user.id)
            if existing2 is None:
                raise
            await self._provision_canvas_and_memory(db=db, user_id=user.id, project_id=existing2.id)
            return existing2

    async def create_project(
        self,
        *,
        user: User,
        title: str,
        kind: ProjectKind,
        description: str | None,
        db: AsyncSession,
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
        created = await self._repo.create(project)
        await self._provision_canvas_and_memory(db=db, user_id=user.id, project_id=created.id)
        return created

    async def list_projects_for_user(self, *, user: User, db: AsyncSession) -> list[ProjectWithCounts]:
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
        combined = [catchall, *ordered]

        for p in combined:
            await self._provision_canvas_and_memory(db=db, user_id=user.id, project_id=p.id)

        counts_map = await self._counts_for_project_ids(db, [p.id for p in combined])
        return [ProjectWithCounts(project=p, counts=counts_map[p.id]) for p in combined]

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

    async def patch_overview(
        self,
        *,
        user: User,
        project_id: UUID,
        fields: OverviewPatchFields,
    ) -> Project:
        project = await self.get_project_or_forbidden(user=user, project_id=project_id)

        if "research_goal" in fields:
            project.research_goal = fields["research_goal"]
        if "research_type" in fields:
            project.research_type = fields["research_type"]
        if "included_topics" in fields:
            project.included_topics = fields["included_topics"] or []
        if "excluded_topics" in fields:
            project.excluded_topics = fields["excluded_topics"] or []
        if "target_entities" in fields:
            project.target_entities = fields["target_entities"] or []
        if "time_horizon" in fields:
            project.time_horizon = fields["time_horizon"]

        return await self._repo.update(project)
