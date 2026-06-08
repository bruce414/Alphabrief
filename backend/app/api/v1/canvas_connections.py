from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.canvas_connection_repository import CanvasConnectionRepository
from app.repositories.canvas_element_repository import CanvasElementRepository
from app.schemas.canvas_connection import (
    CanvasConnectionListResponse,
    CanvasConnectionResponse,
    CreateCanvasConnectionRequest,
    PatchCanvasConnectionRequest,
)
from app.services.canvas_connection_service import CanvasConnectionService


router = APIRouter(tags=["canvas-connections"])


def _to_connection_response(conn: Any) -> CanvasConnectionResponse:
    return CanvasConnectionResponse(
        id=conn.id,
        canvasId=conn.canvas_id,
        fromElementId=conn.from_element_id,
        toElementId=conn.to_element_id,
        label=conn.label,
        connectionType=conn.connection_type,
        styleJson=conn.style_json if conn.style_json is not None else {},
    )


@router.get("/canvases/{canvas_id}/connections", response_model=CanvasConnectionListResponse)
async def list_canvas_connections(
    canvas_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasConnectionListResponse:
    connection_repo = CanvasConnectionRepository(db)
    element_repo = CanvasElementRepository(db)
    svc = CanvasConnectionService(
        db=db,
        connection_repo=connection_repo,
        element_repo=element_repo,
    )
    rows = await svc.list_for_canvas(user_id=current_user.id, canvas_id=canvas_id)
    return CanvasConnectionListResponse(items=[_to_connection_response(c) for c in rows])


@router.post(
    "/canvases/{canvas_id}/connections",
    response_model=CanvasConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_canvas_connection(
    canvas_id: UUID,
    data: CreateCanvasConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasConnectionResponse:
    connection_repo = CanvasConnectionRepository(db)
    element_repo = CanvasElementRepository(db)
    svc = CanvasConnectionService(
        db=db,
        connection_repo=connection_repo,
        element_repo=element_repo,
    )
    conn = await svc.create(
        user_id=current_user.id,
        canvas_id=canvas_id,
        from_element_id=data.from_element_id,
        to_element_id=data.to_element_id,
        label=data.label,
        connection_type=data.connection_type,
        style_json=data.style_json,
    )
    return _to_connection_response(conn)


@router.patch("/canvas-connections/{connection_id}", response_model=CanvasConnectionResponse)
async def patch_canvas_connection(
    connection_id: UUID,
    data: PatchCanvasConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasConnectionResponse:
    connection_repo = CanvasConnectionRepository(db)
    element_repo = CanvasElementRepository(db)
    svc = CanvasConnectionService(
        db=db,
        connection_repo=connection_repo,
        element_repo=element_repo,
    )

    kwargs: dict[str, Any] = {}
    if "label" in data.model_fields_set:
        kwargs["label"] = data.label
    if "connection_type" in data.model_fields_set:
        kwargs["connection_type"] = data.connection_type
    if "style_json" in data.model_fields_set:
        kwargs["style_json"] = data.style_json

    conn = await svc.patch(user_id=current_user.id, connection_id=connection_id, **kwargs)
    return _to_connection_response(conn)


@router.delete("/canvas-connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canvas_connection(
    connection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    connection_repo = CanvasConnectionRepository(db)
    element_repo = CanvasElementRepository(db)
    svc = CanvasConnectionService(
        db=db,
        connection_repo=connection_repo,
        element_repo=element_repo,
    )
    await svc.delete(user_id=current_user.id, connection_id=connection_id)
