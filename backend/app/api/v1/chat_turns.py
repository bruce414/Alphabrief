from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.enums import ChatTurnRole, ChatTurnStatus
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.chat_turn_repository import ChatTurnRepository
from app.schemas.chat_turn import (
    ChatTurnListResponse,
    ChatTurnResponse,
    SendChatMessageRequest,
    SendChatMessageResponse,
)
from app.services.chat_turn_service import send_chat_message


router = APIRouter(tags=["chat_turns"])


def _to_turn_response(turn) -> ChatTurnResponse:
    return ChatTurnResponse(
        id=turn.id,
        chatId=turn.chat_id,
        turnIndex=turn.turn_index,
        role=ChatTurnRole(turn.role),
        status=ChatTurnStatus(turn.status),
        contentMarkdown=turn.content_markdown,
        contentJson=turn.content_json,
        errorCode=turn.error_code,
        errorMessage=turn.error_message,
        modelProvider=turn.model_provider,
        modelName=turn.model_name,
        createdAt=turn.created_at,
        updatedAt=turn.updated_at,
    )


@router.get("/chats/{chat_id}/turns", response_model=ChatTurnListResponse)
async def list_chat_turns(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatTurnListResponse:
    chat_repo = ChatRepository(db)
    chat = await chat_repo.get_by_id(chat_id)
    if chat is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Chat not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if chat.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this chat",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    repo = ChatTurnRepository(db)
    turns = await repo.list_for_chat(chat_id=chat.id)
    return ChatTurnListResponse(items=[_to_turn_response(t) for t in turns])


@router.post("/chats/{chat_id}/turns", response_model=SendChatMessageResponse, status_code=status.HTTP_200_OK)
async def post_chat_turn(
    chat_id: UUID,
    data: SendChatMessageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SendChatMessageResponse:
    user_turn_id, assistant_turn_id, assistant_status = await send_chat_message(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
        content=data.content,
        source_ids=data.source_ids,
        background_tasks=background_tasks,
    )
    return SendChatMessageResponse(
        userTurnId=user_turn_id,
        assistantTurnId=assistant_turn_id,
        assistantStatus=ChatTurnStatus(assistant_status),
    )


@router.get("/chat-turns/{turn_id}", response_model=ChatTurnResponse)
async def get_chat_turn(
    turn_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatTurnResponse:
    repo = ChatTurnRepository(db)
    turn = await repo.get_by_id_via_chat_owner(turn_id=turn_id, user_id=current_user.id)
    if turn is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Chat turn not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return _to_turn_response(turn)

