from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ChatTurnRole, ChatTurnStatus, InputType, IntentType


class ChatTurnResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    chat_id: UUID = Field(alias="chatId")
    turn_index: int = Field(alias="turnIndex")
    role: ChatTurnRole
    status: ChatTurnStatus

    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    content_json: dict[str, Any] | None = Field(default=None, alias="contentJson")

    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")

    model_provider: str | None = Field(default=None, alias="modelProvider")
    model_name: str | None = Field(default=None, alias="modelName")

    detected_input_type: InputType | None = Field(default=None, alias="detectedInputType")
    intent_type: IntentType | None = Field(default=None, alias="intentType")

    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ChatTurnListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ChatTurnResponse]


class SendChatMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str
    source_ids: list[UUID] | None = Field(default=None, alias="sourceIds")


class SendChatMessageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_turn_id: UUID = Field(alias="userTurnId")
    assistant_turn_id: UUID = Field(alias="assistantTurnId")
    assistant_status: ChatTurnStatus = Field(alias="assistantStatus")

    detected_input_type: InputType = Field(alias="detectedInputType")
    detected_intent_type: IntentType = Field(alias="detectedIntentType")
    created_source_ids: list[UUID] = Field(alias="createdSourceIds")
    requires_pre_analysis_warning: bool = Field(default=False, alias="requiresPreAnalysisWarning")

