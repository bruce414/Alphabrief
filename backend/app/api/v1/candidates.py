from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.enums import CandidateStatus, CanvasBlockType, ProvenanceKind
from app.core.errors import AppError
from app.db.session import get_db
from app.models.canvas_block import CanvasBlock
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.candidate_block import CandidateBlock
from app.models.user import User
from app.repositories.canvas_block_repository import CanvasBlockRepository
from app.repositories.candidate_block_repository import CandidateBlockRepository
from app.schemas.canvas_block import CanvasBlockResponse
from app.schemas.candidate_block import (
    CandidateBlockListResponse,
    CandidateBlockResponse,
    PromoteCandidateRequest,
)


router = APIRouter(tags=["candidates"])

_POS_QUANT = Decimal("0.0000000000")


def _pos_str(pos: Decimal) -> str:
    return str(pos.quantize(_POS_QUANT))


def _to_canvas_block_response(block: CanvasBlock) -> CanvasBlockResponse:
    return CanvasBlockResponse(
        id=block.id,
        projectId=block.project_id,
        blockType=CanvasBlockType(block.block_type),
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


def _to_candidate_response(c: CandidateBlock) -> CandidateBlockResponse:
    return CandidateBlockResponse(
        id=c.id,
        chatTurnId=c.chat_turn_id,
        projectId=c.project_id,
        blockType=CanvasBlockType(c.block_type),
        title=c.title,
        contentMarkdown=c.content_markdown,
        status=CandidateStatus(c.status),
    )


@router.get("/chat-turns/{chat_turn_id}/candidates", response_model=CandidateBlockListResponse)
async def list_candidates_for_turn(
    chat_turn_id: UUID,
    includeAll: int = 0,  # noqa: N803 - query param casing per spec
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CandidateBlockListResponse:
    # Owner check via chat_turn -> chat -> user_id.
    stmt = (
        select(ChatTurn)
        .join(Chat, Chat.id == ChatTurn.chat_id)
        .where(ChatTurn.id == chat_turn_id, Chat.user_id == current_user.id)
    )
    turn = (await db.execute(stmt)).scalar_one_or_none()
    if turn is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Chat turn not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    repo = CandidateBlockRepository(db)
    items = await repo.list_for_turn(chat_turn_id=chat_turn_id, include_all=bool(includeAll))
    return CandidateBlockListResponse(items=[_to_candidate_response(i) for i in items])


async def _compute_position_index(
    *,
    repo: CanvasBlockRepository,
    project_id: UUID,
    position_after: UUID | None,
) -> Decimal:
    if position_after is None:
        max_pos = await repo.get_max_active_position(project_id=project_id)
        return (max_pos + Decimal("1.0")) if max_pos is not None else Decimal("1.0")

    after = await repo.get_by_id(position_after)
    if after is None or after.project_id != project_id or after.archived_at is not None:
        raise AppError(
            error_code="INVALID_INPUT",
            message="Invalid positionAfter reference",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    nxt = await repo.get_next_active_after(project_id=project_id, position_index=after.position_index)
    if nxt is None:
        return after.position_index + Decimal("1.0")
    return (after.position_index + nxt.position_index) / Decimal(2)


@router.post("/candidates/{candidate_id}/promote", response_model=CanvasBlockResponse)
async def promote_candidate(
    candidate_id: UUID,
    data: PromoteCandidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasBlockResponse:
    cand_repo = CandidateBlockRepository(db)
    c = await cand_repo.get_by_id(candidate_id)
    if c is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Candidate not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if c.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this candidate",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if c.status == CandidateStatus.DISMISSED.value:
        raise AppError(
            error_code="CANDIDATE_DISMISSED",
            message="Candidate is dismissed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Idempotent promote.
    if c.status == CandidateStatus.PROMOTED.value and c.promoted_block_id is not None:
        block_repo = CanvasBlockRepository(db)
        b = await block_repo.get_by_id(c.promoted_block_id)
        if b is not None:
            return _to_canvas_block_response(b)

    block_type = CanvasBlockType(c.block_type)
    block_repo = CanvasBlockRepository(db)
    pos = await _compute_position_index(repo=block_repo, project_id=c.project_id, position_after=data.position_after)

    block = CanvasBlock(
        project_id=c.project_id,
        user_id=c.user_id,
        block_type=block_type.value,
        title=c.title,
        content_markdown=c.content_markdown,
        content_json={},
        position_index=pos,
        provenance_kind=ProvenanceKind.CHAT_TURN.value,
        provenance_chat_turn_id=c.chat_turn_id,
        provenance_source_id=None,
        confidence_label=None,
        archived_at=None,
        metadata_={},
    )

    db.add(block)
    await db.flush()

    c.status = CandidateStatus.PROMOTED.value
    c.promoted_block_id = block.id
    db.add(c)
    await db.commit()
    await db.refresh(block)
    return _to_canvas_block_response(block)


@router.post("/candidates/{candidate_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    repo = CandidateBlockRepository(db)
    c = await repo.get_by_id(candidate_id)
    if c is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Candidate not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if c.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this candidate",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if c.status != CandidateStatus.DISMISSED.value:
        c.status = CandidateStatus.DISMISSED.value
        db.add(c)
        await db.commit()

    return {"status": "ok"}

