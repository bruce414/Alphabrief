from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.canvas_repository import CanvasRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.canvas import CanvasResponse
from app.services.canvas_service import CanvasService


router = APIRouter(tags=["canvases"])


def _to_canvas_response(canvas: Any) -> CanvasResponse:
    return CanvasResponse(
        id=canvas.id,
        projectId=canvas.project_id,
        title=canvas.title,
        viewportJson=canvas.viewport_json if canvas.viewport_json is not None else {},
        updatedAt=canvas.updated_at,
    )


@router.get("/projects/{project_id}/canvas", response_model=CanvasResponse)
async def get_project_canvas(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasResponse:
    canvas_repo = CanvasRepository(db)
    project_repo = ProjectRepository(db)
    svc = CanvasService(db=db, canvas_repo=canvas_repo, project_repo=project_repo)
    canvas = await svc.get_or_create_for_project(user_id=current_user.id, project_id=project_id)
    return _to_canvas_response(canvas)
