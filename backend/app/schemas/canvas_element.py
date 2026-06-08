from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import CanvasElementType, ProvenanceKind
from app.models.canvas_element import CanvasElement


class CanvasElementResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    canvas_id: UUID = Field(alias="canvasId")
    project_id: UUID = Field(alias="projectId")
    element_type: str = Field(alias="elementType")
    title: str | None = None
    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    content_json: dict[str, Any] = Field(alias="contentJson")
    x: float
    y: float
    width: float | None = None
    height: float | None = None
    z_index: int = Field(alias="zIndex")
    style_json: dict[str, Any] | None = Field(alias="styleJson")
    provenance_kind: str = Field(alias="provenanceKind")
    provenance_chat_turn_id: UUID | None = Field(default=None, alias="provenanceChatTurnId")
    provenance_source_id: UUID | None = Field(default=None, alias="provenanceSourceId")
    archived_at: datetime | None = Field(default=None, alias="archivedAt")


class CanvasElementListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[CanvasElementResponse]


class CreateManualCanvasElementRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    element_type: CanvasElementType = Field(alias="elementType")
    title: str | None = None
    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    content_json: dict[str, Any] | None = Field(default=None, alias="contentJson")
    x: float
    y: float
    width: float | None = None
    height: float | None = None
    style_json: dict[str, Any] | None = Field(default=None, alias="styleJson")
    provenance_kind: ProvenanceKind = Field(default=ProvenanceKind.MANUAL, alias="provenanceKind")

    @field_validator("provenance_kind")
    @classmethod
    def provenance_must_be_manual(cls, v: ProvenanceKind) -> ProvenanceKind:
        if v != ProvenanceKind.MANUAL:
            raise ValueError("Only MANUAL provenance is allowed for this endpoint")
        return v


class CreateCanvasElementFromTurnRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    chat_turn_id: UUID = Field(alias="chatTurnId")
    element_type: CanvasElementType = Field(alias="elementType")
    title: str | None = None
    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    x: float
    y: float
    width: float | None = None
    height: float | None = None


class CreateCanvasElementFromSourceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_id: UUID = Field(alias="sourceId")
    element_type: CanvasElementType = Field(alias="elementType")
    title: str | None = None
    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    x: float
    y: float
    width: float | None = None
    height: float | None = None

    @field_validator("element_type", mode="before")
    @classmethod
    def coerce_element_type(cls, v: Any) -> Any:
        if isinstance(v, CanvasElementType):
            return v
        if isinstance(v, str):
            try:
                return CanvasElementType(v)
            except ValueError:
                pass
        return v

    @field_validator("element_type")
    @classmethod
    def allowed_source_types(cls, v: CanvasElementType) -> CanvasElementType:
        allowed = {
            CanvasElementType.QUOTE,
            CanvasElementType.EVIDENCE,
            CanvasElementType.DATA,
            CanvasElementType.TEXT,
        }
        if v not in allowed:
            raise ValueError("elementType must be QUOTE, EVIDENCE, DATA, or TEXT for from-source")
        return v


class PatchCanvasElementRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    content_markdown: str | None = Field(default=None, alias="contentMarkdown")
    content_json: dict[str, Any] | None = Field(default=None, alias="contentJson")
    element_type: CanvasElementType | None = Field(default=None, alias="elementType")
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    z_index: int | None = Field(default=None, alias="zIndex")
    style_json: dict[str, Any] | None = Field(default=None, alias="styleJson")
    archived: bool | None = None


def canvas_element_model_to_response(element: CanvasElement) -> CanvasElementResponse:
    """Map a persisted CanvasElement ORM row to the public API response shape."""

    def _dec_to_float(d: Decimal | None) -> float | None:
        if d is None:
            return None
        return float(d)

    return CanvasElementResponse(
        id=element.id,
        canvasId=element.canvas_id,
        projectId=element.project_id,
        elementType=element.element_type,
        title=element.title,
        contentMarkdown=element.content_markdown,
        contentJson=element.content_json or {},
        x=float(element.x),
        y=float(element.y),
        width=_dec_to_float(element.width),
        height=_dec_to_float(element.height),
        zIndex=element.z_index,
        styleJson=element.style_json if element.style_json is not None else {},
        provenanceKind=element.provenance_kind,
        provenanceChatTurnId=element.provenance_chat_turn_id,
        provenanceSourceId=element.provenance_source_id,
        archivedAt=element.archived_at,
    )
