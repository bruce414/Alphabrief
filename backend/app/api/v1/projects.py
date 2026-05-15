from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.source import Source
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    CreateProjectRequest,
    PatchProjectRequest,
    ProjectListResponse,
    ProjectResponse,
)
from app.schemas.project_overview import (
    OverviewResponse,
    OverviewStatusResponse,
    PatchOverviewRequest,
)
from app.schemas.source import SourceListResponse, SourceSummaryResponse
from app.services.project_service import OverviewPatchFields, ProjectCounts, ProjectService
from app.services.update_check_service import run_update_check


router = APIRouter(prefix="/projects", tags=["projects"])


def _jsonb_str_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, str)]
    return []


def _to_project_response(project, counts: ProjectCounts) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        kind=project.kind,
        title=project.title,
        description=project.description,
        archivedAt=project.archived_at,
        createdAt=project.created_at,
        updatedAt=project.updated_at,
        chatCount=counts.chat_count,
        canvasElementCount=counts.canvas_element_count,
        sourceCount=counts.source_count,
        briefCount=counts.brief_count,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    project = await svc.create_project(
        user=current_user,
        title=data.title,
        kind=data.kind,
        description=data.description,
        db=db,
    )
    counts = await svc.counts_for_single_project(db=db, project_id=project.id)
    return _to_project_response(project, counts)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    items = await svc.list_projects_for_user(user=current_user, db=db)
    return ProjectListResponse(items=[_to_project_response(row.project, row.counts) for row in items])


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    project = await svc.get_project_or_forbidden(user=current_user, project_id=project_id)
    await svc.ensure_canvas_and_memory_for_project(user=current_user, project_id=project_id, db=db)
    counts = await svc.counts_for_single_project(db=db, project_id=project.id)
    return _to_project_response(project, counts)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def patch_project(
    project_id: UUID,
    data: PatchProjectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    if data.title is not None and not data.title.strip():
        raise AppError(
            error_code="INVALID_INPUT",
            message="Invalid input",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    project = await svc.patch_project(
        user=current_user,
        project_id=project_id,
        title=data.title,
        description=data.description,
        archived=data.archived,
    )
    counts = await svc.counts_for_single_project(db=db, project_id=project.id)
    return _to_project_response(project, counts)


def _to_overview_response(project, counts: ProjectCounts) -> OverviewResponse:
    return OverviewResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        researchGoal=project.research_goal,
        researchType=project.research_type,
        includedTopics=_jsonb_str_list(project.included_topics),
        excludedTopics=_jsonb_str_list(project.excluded_topics),
        targetEntities=_jsonb_str_list(project.target_entities),
        timeHorizon=project.time_horizon,
        createdAt=project.created_at,
        updatedAt=project.updated_at,
        status=OverviewStatusResponse(
            totalNodes=counts.canvas_element_count,
            totalSources=counts.source_count,
            openQuestionsCount=0,
            unsupportedClaimsCount=0,
            updatesAvailableCount=project.updates_available_count,
            lastCheckedAt=project.last_checked_at,
        ),
    )


@router.get("/{project_id}/overview", response_model=OverviewResponse)
async def get_project_overview(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverviewResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    project = await svc.get_project_or_forbidden(user=current_user, project_id=project_id)
    counts = await svc.counts_for_single_project(db=db, project_id=project.id)
    return _to_overview_response(project, counts)


@router.post("/{project_id}/overview/check-updates", response_model=OverviewResponse)
async def check_project_overview_updates(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverviewResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    await svc.get_project_or_forbidden(user=current_user, project_id=project_id)
    project = await run_update_check(db, project_id)
    counts = await svc.counts_for_single_project(db=db, project_id=project.id)
    return _to_overview_response(project, counts)


@router.patch("/{project_id}/overview", response_model=OverviewResponse)
async def patch_project_overview(
    project_id: UUID,
    data: PatchOverviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverviewResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)

    fields: OverviewPatchFields = {}
    if "research_goal" in data.model_fields_set:
        fields["research_goal"] = data.research_goal
    if "research_type" in data.model_fields_set:
        fields["research_type"] = data.research_type
    if "included_topics" in data.model_fields_set:
        fields["included_topics"] = data.included_topics
    if "excluded_topics" in data.model_fields_set:
        fields["excluded_topics"] = data.excluded_topics
    if "target_entities" in data.model_fields_set:
        fields["target_entities"] = data.target_entities
    if "time_horizon" in data.model_fields_set:
        fields["time_horizon"] = data.time_horizon

    project = await svc.patch_overview(
        user=current_user, project_id=project_id, fields=fields
    )
    counts = await svc.counts_for_single_project(db=db, project_id=project.id)
    return _to_overview_response(project, counts)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    await svc.delete_project(user=current_user, project_id=project_id)


def _origin_for_source(src: Source) -> str:
    if isinstance(src.metadata_, dict):
        origin = src.metadata_.get("origin")
        if isinstance(origin, str) and origin:
            return origin
    if src.source_access_method == "WEB_SEARCH":
        return "ai_web_search"
    return "user"


def _to_summary(src: Source) -> SourceSummaryResponse:
    return SourceSummaryResponse(
        id=src.id,
        projectId=src.project_id,
        sourceType=src.source_type,
        sourceAccessMethod=src.source_access_method,
        sourceAccessStatus=src.source_access_status,
        normalizedUrl=src.normalized_url,
        title=src.title,
        publisher=src.publisher,
        origin=_origin_for_source(src),
        createdAt=src.created_at,
    )


@router.get("/{project_id}/sources", response_model=SourceListResponse)
async def list_project_sources(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SourceListResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    project = await svc.get_project_or_forbidden(user=current_user, project_id=project_id)

    rows = list(
        (
            await db.execute(
                select(Source)
                .where(Source.user_id == current_user.id, Source.project_id == project.id)
                .order_by(Source.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return SourceListResponse(items=[_to_summary(s) for s in rows])

