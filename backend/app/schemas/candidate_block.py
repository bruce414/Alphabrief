from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CandidateStatus, CanvasBlockType


class CandidateBlockResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    chat_turn_id: UUID = Field(alias="chatTurnId")
    project_id: UUID = Field(alias="projectId")
    block_type: CanvasBlockType = Field(alias="blockType")
    title: str | None = None
    content_markdown: str = Field(alias="contentMarkdown")
    status: CandidateStatus


class CandidateBlockListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[CandidateBlockResponse]


class PromoteCandidateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    position_after: UUID | None = Field(default=None, alias="positionAfter")

