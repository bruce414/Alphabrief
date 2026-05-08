from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.enums import ChatStatus, ProjectKind
from app.core.errors import AppError
from app.db.session import get_db
from app.models.chat import Chat
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.chat import (
    ChatDetailResponse,
    ChatListResponse,
    ChatProjectSummary,
    ChatResponse,
    CreateChatRequest,
    PatchChatRequest,
)
from app.services.project_service import ProjectService


router = APIRouter(tags=["chats"])


def _to_chat_response(chat: Chat) -> ChatResponse:
    return ChatResponse(
        id=chat.id,
        projectId=chat.project_id,
        title=chat.title,
        status=ChatStatus(chat.status),
        lastTurnAt=chat.last_turn_at,
        createdAt=chat.created_at,
    )


@router.post("/projects/{project_id}/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    project_id: UUID,
    data: CreateChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    project_repo = ProjectRepository(db)
    project_svc = ProjectService(project_repo)
    project = await project_svc.get_project_or_forbidden(user=current_user, project_id=project_id)

    title = (data.title or "").strip() or "New chat"
    chat = Chat(
        project_id=project.id,
        user_id=current_user.id,
        title=title,
        status="ACTIVE",
        last_turn_at=None,
        metadata_={},
    )
    repo = ChatRepository(db)
    created = await repo.create(chat)
    return _to_chat_response(created)


@router.get("/projects/{project_id}/chats", response_model=ChatListResponse)
async def list_chats(
    project_id: UUID,
    cursor: UUID | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    include_archived: int = Query(default=0, alias="includeArchived"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatListResponse:
    project_repo = ProjectRepository(db)
    project_svc = ProjectService(project_repo)
    project = await project_svc.get_project_or_forbidden(user=current_user, project_id=project_id)

    repo = ChatRepository(db)
    cursor_chat: Chat | None = None
    if cursor is not None:
        cursor_chat = await repo.get_by_id_for_user(chat_id=cursor, user_id=current_user.id)
        if cursor_chat is None or cursor_chat.project_id != project.id:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid cursor",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    items = await repo.list_for_project(
        project_id=project.id,
        include_archived=bool(include_archived),
        limit=limit,
        cursor_chat=cursor_chat,
    )

    next_cursor = items[-1].id if len(items) == limit else None
    return ChatListResponse(items=[_to_chat_response(c) for c in items], nextCursor=next_cursor)


@router.get("/chats/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatDetailResponse:
    repo = ChatRepository(db)
    chat = await repo.get_by_id(chat_id)
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

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(chat.project_id)
    if project is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Project not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return ChatDetailResponse(
        chat=_to_chat_response(chat),
        project=ChatProjectSummary(id=project.id, kind=ProjectKind(project.kind), title=project.title),
    )


@router.patch("/chats/{chat_id}", response_model=ChatResponse)
async def patch_chat(
    chat_id: UUID,
    data: PatchChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    repo = ChatRepository(db)
    chat = await repo.get_by_id(chat_id)
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

    if data.title is not None:
        if not data.title.strip():
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        chat.title = data.title
    if data.status is not None:
        chat.status = data.status.value

    updated = await repo.update(chat)
    return _to_chat_response(updated)


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    repo = ChatRepository(db)
    chat = await repo.get_by_id(chat_id)
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
    await repo.delete(chat)

