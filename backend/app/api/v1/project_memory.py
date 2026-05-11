from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.project_memory_repository import ProjectMemoryRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_memory import PatchProjectMemoryRequest, ProjectMemoryResponse, RefreshProjectMemoryRequest
from app.services.project_memory_service import ProjectMemoryService


router = APIRouter(tags=["project-memory"])


def _memory_field_as_list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    return []


def _to_project_memory_response(memory: Any) -> ProjectMemoryResponse:
    return ProjectMemoryResponse(
        id=memory.id,
        projectId=memory.project_id,
        summaryMarkdown=memory.summary_markdown,
        entities=_memory_field_as_list(memory.entities_json),
        themes=_memory_field_as_list(memory.themes_json),
        openQuestions=_memory_field_as_list(memory.open_questions_json),
        conclusions=_memory_field_as_list(memory.conclusions_json),
        updatedAt=memory.updated_at,
    )


@router.get("/projects/{project_id}/memory", response_model=ProjectMemoryResponse)
async def get_project_memory(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemoryResponse:
    repo = ProjectMemoryRepository(db)
    project_repo = ProjectRepository(db)
    svc = ProjectMemoryService(db=db, repo=repo, project_repo=project_repo)
    memory = await svc.get_or_create(user_id=current_user.id, project_id=project_id)
    return _to_project_memory_response(memory)


@router.patch("/projects/{project_id}/memory", response_model=ProjectMemoryResponse)
async def patch_project_memory(
    project_id: UUID,
    data: PatchProjectMemoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemoryResponse:
    repo = ProjectMemoryRepository(db)
    project_repo = ProjectRepository(db)
    svc = ProjectMemoryService(db=db, repo=repo, project_repo=project_repo)

    kwargs: dict[str, Any] = {}
    if "summary_markdown" in data.model_fields_set:
        kwargs["summary_markdown"] = data.summary_markdown
    if "entities" in data.model_fields_set:
        kwargs["entities"] = data.entities
    if "themes" in data.model_fields_set:
        kwargs["themes"] = data.themes
    if "open_questions" in data.model_fields_set:
        kwargs["open_questions"] = data.open_questions
    if "conclusions" in data.model_fields_set:
        kwargs["conclusions"] = data.conclusions

    memory = await svc.patch(user_id=current_user.id, project_id=project_id, **kwargs)
    return _to_project_memory_response(memory)


@router.post("/projects/{project_id}/memory/refresh")
async def refresh_project_memory(
    project_id: UUID,
    _data: RefreshProjectMemoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Reserved for AI-backed refresh (API_SPEC §13); not implemented in v0.3."""

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if project is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Project not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if project.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this project",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "AI memory refresh is not available yet.",
            },
        },
    )
