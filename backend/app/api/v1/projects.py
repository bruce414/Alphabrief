from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    CreateProjectRequest,
    PatchProjectRequest,
    ProjectListResponse,
    ProjectResponse,
)
from app.services.project_service import ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


def _to_project_response(project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        kind=project.kind,
        title=project.title,
        description=project.description,
        archivedAt=project.archived_at,
        createdAt=project.created_at,
        updatedAt=project.updated_at,
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
    )
    return _to_project_response(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    items = await svc.list_projects_for_user(user=current_user, db=db)
    return ProjectListResponse(items=[_to_project_response(p) for p in items])


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    project = await svc.get_project_or_forbidden(user=current_user, project_id=project_id)
    return _to_project_response(project)


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
    return _to_project_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    repo = ProjectRepository(db)
    svc = ProjectService(repo)
    await svc.delete_project(user=current_user, project_id=project_id)

