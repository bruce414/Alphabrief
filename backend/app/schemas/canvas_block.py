from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CanvasBlockType


class CanvasBlockResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    project_id: UUID = Field(alias="projectId")
    block_type: CanvasBlockType = Field(alias="blockType")
    title: str | None = None
    content_markdown: str = Field(alias="contentMarkdown")
    content_json: dict[str, Any] = Field(alias="contentJson")
    position_index: str = Field(alias="positionIndex")
    provenance_kind: str = Field(alias="provenanceKind")
    provenance_chat_turn_id: UUID | None = Field(default=None, alias="provenanceChatTurnId")
    provenance_source_id: UUID | None = Field(default=None, alias="provenanceSourceId")
    archived_at: datetime | None = Field(default=None, alias="archivedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class CanvasBlockListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[CanvasBlockResponse]
    should_suggest_project_conversion: bool = Field(alias="shouldSuggestProjectConversion")


class CreateManualCanvasBlockRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    block_type: CanvasBlockType = Field(alias="blockType")
    content_markdown: str = Field(alias="contentMarkdown", min_length=1)
    title: str | None = None
    content_json: dict[str, Any] | None = Field(default=None, alias="contentJson")
    position_after: UUID | None = Field(default=None, alias="positionAfter")


class CreateCanvasBlockFromTurnRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    chat_turn_id: UUID = Field(alias="chatTurnId")
    block_type: CanvasBlockType = Field(alias="blockType")
    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    title: str | None = None
    position_after: UUID | None = Field(default=None, alias="positionAfter")


class CreateCanvasBlockFromSourceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_id: UUID = Field(alias="sourceId")
    block_type: Literal["QUOTE", "SUMMARY", "NOTE"] = Field(alias="blockType")
    content_markdown: str = Field(alias="contentMarkdown", min_length=1)
    title: str | None = None
    position_after: UUID | None = Field(default=None, alias="positionAfter")


class PatchCanvasBlockRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    block_type: CanvasBlockType | None = Field(default=None, alias="blockType")
    title: str | None = None
    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    content_json: dict[str, Any] | None = Field(default=None, alias="contentJson")
    archived: bool | None = None
    position_after: UUID | None = Field(default=None, alias="positionAfter")

