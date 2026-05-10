from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CandidateStatus, CanvasElementType


class CandidateElementResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    chat_turn_id: UUID = Field(alias="chatTurnId")
    project_id: UUID = Field(alias="projectId")
    suggested_element_type: CanvasElementType = Field(alias="suggestedElementType")
    title: str | None = None
    content_markdown: str = Field(alias="contentMarkdown")
    content_json: dict[str, Any] = Field(alias="contentJson")
    status: CandidateStatus


class CandidateElementListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[CandidateElementResponse]


class PromoteCandidateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    canvas_id: UUID = Field(alias="canvasId")
    element_type: CanvasElementType = Field(alias="elementType")
    title: str | None = None
    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    x: float
    y: float
    width: float | None = None
    height: float | None = None
