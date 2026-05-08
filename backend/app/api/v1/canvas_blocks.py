from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.enums import CanvasBlockType
from app.db.session import get_db
from app.models.user import User
from app.repositories.canvas_block_repository import CanvasBlockRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.canvas_block import (
    CanvasBlockListResponse,
    CanvasBlockResponse,
    CreateCanvasBlockFromSourceRequest,
    CreateCanvasBlockFromTurnRequest,
    CreateManualCanvasBlockRequest,
    PatchCanvasBlockRequest,
)
from app.services.canvas_block_service import CanvasBlockService


router = APIRouter(tags=["canvas-blocks"])


_POS_QUANT = Decimal("0.0000000000")


def _pos_str(pos: Decimal) -> str:
    return str(pos.quantize(_POS_QUANT))


def _to_canvas_block_response(block) -> CanvasBlockResponse:
    return CanvasBlockResponse(
        id=block.id,
        projectId=block.project_id,
        blockType=block.block_type,
        title=block.title,
        contentMarkdown=block.content_markdown,
        contentJson=block.content_json,
        positionIndex=_pos_str(block.position_index),
        provenanceKind=block.provenance_kind,
        provenanceChatTurnId=block.provenance_chat_turn_id,
        provenanceSourceId=block.provenance_source_id,
        archivedAt=block.archived_at,
        createdAt=block.created_at,
        updatedAt=block.updated_at,
    )


@router.post(
    "/projects/{project_id}/canvas-blocks",
    response_model=CanvasBlockResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_canvas_block(
    project_id: UUID,
    data: CreateManualCanvasBlockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasBlockResponse:
    repo = CanvasBlockRepository(db)
    project_repo = ProjectRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasBlockService(db=db, repo=repo, project_repo=project_repo, source_repo=source_repo)
    block = await svc.create_manual_block(
        user_id=current_user.id,
        project_id=project_id,
        block_type=data.block_type,
        title=data.title,
        content_markdown=data.content_markdown,
        content_json=data.content_json,
        position_after=data.position_after,
    )
    return _to_canvas_block_response(block)


@router.post(
    "/projects/{project_id}/canvas-blocks/from-turn",
    response_model=CanvasBlockResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_canvas_block_from_turn(
    project_id: UUID,
    data: CreateCanvasBlockFromTurnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasBlockResponse:
    repo = CanvasBlockRepository(db)
    project_repo = ProjectRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasBlockService(db=db, repo=repo, project_repo=project_repo, source_repo=source_repo)
    block = await svc.create_from_turn(
        user_id=current_user.id,
        project_id=project_id,
        chat_turn_id=data.chat_turn_id,
        block_type=data.block_type,
        title=data.title,
        content_markdown=data.content_markdown,
        position_after=data.position_after,
    )
    return _to_canvas_block_response(block)


@router.post(
    "/projects/{project_id}/canvas-blocks/from-source",
    response_model=CanvasBlockResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_canvas_block_from_source(
    project_id: UUID,
    data: CreateCanvasBlockFromSourceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasBlockResponse:
    repo = CanvasBlockRepository(db)
    project_repo = ProjectRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasBlockService(db=db, repo=repo, project_repo=project_repo, source_repo=source_repo)
    block = await svc.create_from_source(
        user_id=current_user.id,
        project_id=project_id,
        source_id=data.source_id,
        block_type=CanvasBlockType(data.block_type),
        title=data.title,
        content_markdown=data.content_markdown,
        position_after=data.position_after,
    )
    return _to_canvas_block_response(block)


@router.get("/projects/{project_id}/canvas-blocks", response_model=CanvasBlockListResponse)
async def list_canvas_blocks(
    project_id: UUID,
    includeArchived: int = 0,  # noqa: N803 - query param casing per spec
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasBlockListResponse:
    repo = CanvasBlockRepository(db)
    project_repo = ProjectRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasBlockService(db=db, repo=repo, project_repo=project_repo, source_repo=source_repo)
    items, suggest = await svc.list_blocks_for_project(
        user_id=current_user.id,
        project_id=project_id,
        include_archived=bool(includeArchived),
    )
    return CanvasBlockListResponse(
        items=[_to_canvas_block_response(b) for b in items],
        shouldSuggestProjectConversion=suggest,
    )


@router.patch("/canvas-blocks/{block_id}", response_model=CanvasBlockResponse)
async def patch_canvas_block(
    block_id: UUID,
    data: PatchCanvasBlockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasBlockResponse:
    repo = CanvasBlockRepository(db)
    project_repo = ProjectRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasBlockService(db=db, repo=repo, project_repo=project_repo, source_repo=source_repo)

    reposition = "position_after" in data.model_fields_set

    block = await svc.patch_block(
        user_id=current_user.id,
        block_id=block_id,
        block_type=data.block_type,
        title=data.title,
        content_markdown=data.content_markdown,
        content_json=data.content_json,
        archived=data.archived,
        position_after=data.position_after,
        reposition=reposition,
    )
    return _to_canvas_block_response(block)


@router.delete("/canvas-blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canvas_block(
    block_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    repo = CanvasBlockRepository(db)
    project_repo = ProjectRepository(db)
    source_repo = SourceRepository(db)
    svc = CanvasBlockService(db=db, repo=repo, project_repo=project_repo, source_repo=source_repo)
    await svc.delete_block(user_id=current_user.id, block_id=block_id)

