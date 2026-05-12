from __future__ import annotations

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
from app.schemas.source import SourceListResponse, SourceSummaryResponse
from app.services.project_service import ProjectCounts, ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


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

