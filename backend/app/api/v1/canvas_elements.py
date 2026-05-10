from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.canvas_element_repository import CanvasElementRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.canvas_element import (
    CanvasElementListResponse,
    CanvasElementResponse,
    CreateCanvasElementFromSourceRequest,
    CreateCanvasElementFromTurnRequest,
    CreateManualCanvasElementRequest,
    PatchCanvasElementRequest,
)
from app.services.canvas_element_service import CanvasElementService


router = APIRouter(tags=["canvas-elements"])


def _dec(value: float | int | Decimal | None) -> Decimal:
    return Decimal(str(value))


def _dec_opt(value: float | int | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _to_float(d: Decimal | None) -> float | None:
    if d is None:
        return None
    return float(d)


def _to_element_response(element: Any) -> CanvasElementResponse:
    return CanvasElementResponse(
        id=element.id,
        canvasId=element.canvas_id,
        projectId=element.project_id,
        elementType=element.element_type,
        title=element.title,
        contentMarkdown=element.content_markdown,
        contentJson=element.content_json or {},
        x=float(element.x),
        y=float(element.y),
        width=_to_float(element.width),
        height=_to_float(element.height),
        zIndex=element.z_index,
        styleJson=element.style_json if element.style_json is not None else {},
        provenanceKind=element.provenance_kind,
        provenanceChatTurnId=element.provenance_chat_turn_id,
        provenanceSourceId=element.provenance_source_id,
        archivedAt=element.archived_at,
    )


@router.get("/canvases/{canvas_id}/elements", response_model=CanvasElementListResponse)
async def list_canvas_elements(
    canvas_id: UUID,
    includeArchived: int = 0,  # noqa: N803
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasElementListResponse:
    element_repo = CanvasElementRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasElementService(db=db, element_repo=element_repo, source_repo=source_repo)
    rows = await svc.list_for_canvas(
        user_id=current_user.id,
        canvas_id=canvas_id,
        include_archived=bool(includeArchived),
    )
    return CanvasElementListResponse(items=[_to_element_response(e) for e in rows])


@router.post(
    "/canvases/{canvas_id}/elements",
    response_model=CanvasElementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_canvas_element(
    canvas_id: UUID,
    data: CreateManualCanvasElementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasElementResponse:
    element_repo = CanvasElementRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasElementService(db=db, element_repo=element_repo, source_repo=source_repo)
    element = await svc.create_manual(
        user_id=current_user.id,
        canvas_id=canvas_id,
        element_type=data.element_type,
        title=data.title,
        content_markdown=data.content_markdown,
        content_json=data.content_json,
        x=_dec(data.x),
        y=_dec(data.y),
        width=_dec_opt(data.width),
        height=_dec_opt(data.height),
        style_json=data.style_json,
    )
    return _to_element_response(element)


@router.post(
    "/canvases/{canvas_id}/elements/from-turn",
    response_model=CanvasElementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_canvas_element_from_turn(
    canvas_id: UUID,
    data: CreateCanvasElementFromTurnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasElementResponse:
    element_repo = CanvasElementRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasElementService(db=db, element_repo=element_repo, source_repo=source_repo)
    element = await svc.create_from_turn(
        user_id=current_user.id,
        canvas_id=canvas_id,
        chat_turn_id=data.chat_turn_id,
        element_type=data.element_type,
        title=data.title,
        content_markdown=data.content_markdown,
        x=_dec(data.x),
        y=_dec(data.y),
        width=_dec_opt(data.width),
        height=_dec_opt(data.height),
    )
    return _to_element_response(element)


@router.post(
    "/canvases/{canvas_id}/elements/from-source",
    response_model=CanvasElementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_canvas_element_from_source(
    canvas_id: UUID,
    data: CreateCanvasElementFromSourceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasElementResponse:
    element_repo = CanvasElementRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasElementService(db=db, element_repo=element_repo, source_repo=source_repo)
    element = await svc.create_from_source(
        user_id=current_user.id,
        canvas_id=canvas_id,
        source_id=data.source_id,
        element_type=data.element_type,
        title=data.title,
        content_markdown=data.content_markdown,
        x=_dec(data.x),
        y=_dec(data.y),
        width=_dec_opt(data.width),
        height=_dec_opt(data.height),
    )
    return _to_element_response(element)


@router.patch("/canvas-elements/{element_id}", response_model=CanvasElementResponse)
async def patch_canvas_element(
    element_id: UUID,
    data: PatchCanvasElementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasElementResponse:
    element_repo = CanvasElementRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasElementService(db=db, element_repo=element_repo, source_repo=source_repo)

    partial: dict[str, Any] = {}
    if "title" in data.model_fields_set:
        partial["title"] = data.title
    if "content_markdown" in data.model_fields_set:
        partial["content_markdown"] = data.content_markdown
    if "content_json" in data.model_fields_set:
        partial["content_json"] = data.content_json
    if "element_type" in data.model_fields_set:
        partial["element_type"] = data.element_type
    if "x" in data.model_fields_set:
        if data.x is None:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        partial["x"] = _dec(data.x)
    if "y" in data.model_fields_set:
        if data.y is None:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        partial["y"] = _dec(data.y)
    if "width" in data.model_fields_set:
        partial["width"] = _dec_opt(data.width)
    if "height" in data.model_fields_set:
        partial["height"] = _dec_opt(data.height)
    if "z_index" in data.model_fields_set:
        partial["z_index"] = data.z_index
    if "style_json" in data.model_fields_set:
        partial["style_json"] = data.style_json
    if "archived" in data.model_fields_set:
        partial["archived"] = data.archived

    element = await svc.patch(user_id=current_user.id, element_id=element_id, **partial)
    return _to_element_response(element)


@router.delete("/canvas-elements/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canvas_element(
    element_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    element_repo = CanvasElementRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasElementService(db=db, element_repo=element_repo, source_repo=source_repo)
    await svc.delete(user_id=current_user.id, element_id=element_id)
