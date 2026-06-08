from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.enums import CandidateStatus, CanvasElementType
from app.core.errors import AppError
from app.db.session import get_db
from app.models.candidate_element import CandidateElement
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.user import User
from app.repositories.canvas_connection_repository import CanvasConnectionRepository
from app.repositories.canvas_element_repository import CanvasElementRepository
from app.repositories.candidate_element_repository import CandidateElementRepository
from app.repositories.source_repository import SourceRepository
from app.services.canvas_connection_service import (
    ALLOWED_PROPOSAL_EDGE_TYPES,
    CanvasConnectionService,
)
from app.schemas.canvas_element import CanvasElementResponse, canvas_element_model_to_response
from app.schemas.candidate_element import (
    CandidateElementListResponse,
    CandidateElementResponse,
    PromoteCandidateRequest,
)
from app.services.canvas_element_service import CanvasElementService


router = APIRouter(tags=["candidates"])


def _dec(value: float | int | Decimal) -> Decimal:
    return Decimal(str(value))


def _dec_opt(value: float | int | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _to_candidate_element_response(c: CandidateElement) -> CandidateElementResponse:
    return CandidateElementResponse(
        id=c.id,
        chatTurnId=c.chat_turn_id,
        projectId=c.project_id,
        suggestedElementType=CanvasElementType(c.suggested_element_type),
        title=c.title,
        contentMarkdown=c.content_markdown,
        contentJson=c.content_json or {},
        status=CandidateStatus(c.status),
    )


@router.get("/chat-turns/{chat_turn_id}/candidates", response_model=CandidateElementListResponse)
async def list_candidates_for_turn(
    chat_turn_id: UUID,
    includeAll: int = 0,  # noqa: N803 - query param casing per spec
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CandidateElementListResponse:
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

    repo = CandidateElementRepository(db)
    items = await repo.list_for_turn(chat_turn_id=chat_turn_id, include_all=bool(includeAll))
    return CandidateElementListResponse(items=[_to_candidate_element_response(i) for i in items])


@router.post(
    "/candidates/{candidate_id}/promote",
    response_model=CanvasElementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def promote_candidate(
    candidate_id: UUID,
    data: PromoteCandidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CanvasElementResponse:
    cand_repo = CandidateElementRepository(db)
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

    element_repo = CanvasElementRepository(db)
    if c.status == CandidateStatus.PROMOTED.value and c.promoted_element_id is not None:
        existing = await element_repo.get_by_id(c.promoted_element_id)
        if existing is not None:
            return canvas_element_model_to_response(existing)

    resolved_md = (data.content_markdown or c.content_markdown) or ""
    if not (resolved_md or "").strip():
        raise AppError(
            error_code="INVALID_INPUT",
            message="Invalid input",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    resolved_title = c.title
    if "title" in data.model_fields_set:
        resolved_title = data.title

    source_repo = SourceRepository(db)
    svc = CanvasElementService(db=db, element_repo=element_repo, source_repo=source_repo)
    element = await svc.create_from_candidate(
        user_id=current_user.id,
        canvas_id=data.canvas_id,
        candidate=c,
        element_type=data.element_type,
        title=resolved_title,
        content_markdown=resolved_md,
        x=_dec(data.x),
        y=_dec(data.y),
        width=_dec_opt(data.width),
        height=_dec_opt(data.height),
        commit=False,
    )

    proposed_edge = (c.content_json or {}).get("proposed_edge")
    if isinstance(proposed_edge, dict):
        edge_type = str(proposed_edge.get("edge_type") or "").strip().lower()
        target_raw = proposed_edge.get("target_element_id")
        try:
            target_element_id = UUID(str(target_raw)) if target_raw else None
        except (TypeError, ValueError):
            target_element_id = None
        if (
            target_element_id is not None
            and edge_type in ALLOWED_PROPOSAL_EDGE_TYPES
        ):
            conn_repo = CanvasConnectionRepository(db)
            connection_svc = CanvasConnectionService(
                db=db,
                connection_repo=conn_repo,
                element_repo=element_repo,
            )
            await connection_svc.create(
                user_id=current_user.id,
                canvas_id=data.canvas_id,
                from_element_id=element.id,
                to_element_id=target_element_id,
                label=None,
                connection_type=edge_type,
                style_json=None,
                commit=False,
            )

    c.status = CandidateStatus.PROMOTED.value
    c.promoted_element_id = element.id
    db.add(c)
    await db.commit()
    await db.refresh(element)

    return canvas_element_model_to_response(element)


@router.post("/candidates/{candidate_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    repo = CandidateElementRepository(db)
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
        await repo.update(c)

    return {"status": "ok"}
