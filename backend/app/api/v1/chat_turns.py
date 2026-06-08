from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.api.deps import get_current_user, get_http_client
from app.core.enums import ChatTurnRole, ChatTurnStatus, InputType, IntentType
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.chat_turn_repository import ChatTurnRepository
from app.schemas.chat_turn import (
    AssistantTurnActionResponse,
    ChatTurnListResponse,
    ChatTurnResponse,
    SendChatMessageRequest,
    SendChatMessageResponse,
)
from app.services.chat_turn_service import (
    regenerate_assistant_turn,
    send_chat_message,
    stop_assistant_generation,
)


router = APIRouter(tags=["chat_turns"])


def _graph_context_node_count_from_turn(turn) -> int | None:
    content_json = turn.content_json
    if not isinstance(content_json, dict):
        return None
    value = content_json.get("graphContextNodeCount")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


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
        detectedInputType=InputType(turn.detected_input_type) if turn.detected_input_type else None,
        intentType=IntentType(turn.intent_type) if turn.intent_type else None,
        graphContextNodeCount=_graph_context_node_count_from_turn(turn),
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
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> SendChatMessageResponse:
    (
        user_turn_id,
        assistant_turn_id,
        assistant_status,
        detected_input_type,
        intent_type,
        created_source_ids,
        graph_context_node_count,
    ) = await send_chat_message(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
        content=data.content,
        source_ids=data.source_ids,
        research_mode=data.research_mode,
        background_tasks=background_tasks,
        http_client=http_client,
    )
    return SendChatMessageResponse(
        userTurnId=user_turn_id,
        assistantTurnId=assistant_turn_id,
        assistantStatus=ChatTurnStatus(assistant_status),
        detectedInputType=InputType(detected_input_type),
        detectedIntentType=IntentType(intent_type),
        createdSourceIds=created_source_ids,
        requiresPreAnalysisWarning=False,
        graphContextNodeCount=graph_context_node_count,
    )


@router.post(
    "/chat-turns/{turn_id}/stop",
    response_model=AssistantTurnActionResponse,
    status_code=status.HTTP_200_OK,
)
async def stop_chat_turn_generation(
    turn_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistantTurnActionResponse:
    turn = await stop_assistant_generation(
        db=db,
        current_user=current_user,
        assistant_turn_id=turn_id,
    )
    return AssistantTurnActionResponse(
        assistantTurnId=turn.id,
        assistantStatus=ChatTurnStatus(turn.status),
    )


@router.post(
    "/chat-turns/{turn_id}/regenerate",
    response_model=AssistantTurnActionResponse,
    status_code=status.HTTP_200_OK,
)
async def regenerate_chat_turn(
    turn_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistantTurnActionResponse:
    turn = await regenerate_assistant_turn(
        db=db,
        current_user=current_user,
        assistant_turn_id=turn_id,
        background_tasks=background_tasks,
    )
    return AssistantTurnActionResponse(
        assistantTurnId=turn.id,
        assistantStatus=ChatTurnStatus(turn.status),
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

