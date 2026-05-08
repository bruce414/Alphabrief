from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ChatStatus, ProjectKind


class CreateChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None


class PatchChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    status: ChatStatus | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    project_id: UUID = Field(alias="projectId")
    title: str
    status: ChatStatus
    last_turn_at: datetime | None = Field(default=None, alias="lastTurnAt")
    created_at: datetime = Field(alias="createdAt")


class ChatListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ChatResponse]
    next_cursor: UUID | None = Field(default=None, alias="nextCursor")


class ChatProjectSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    kind: ProjectKind
    title: str


class ChatDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    chat: ChatResponse
    project: ChatProjectSummary

