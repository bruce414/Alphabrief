from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ConnectionType


class CanvasConnectionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    canvas_id: UUID = Field(alias="canvasId")
    from_element_id: UUID = Field(alias="fromElementId")
    to_element_id: UUID = Field(alias="toElementId")
    label: str | None = None
    connection_type: str = Field(alias="connectionType")
    style_json: dict[str, Any] | None = Field(alias="styleJson")


class CanvasConnectionListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[CanvasConnectionResponse]


class CreateCanvasConnectionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_element_id: UUID = Field(alias="fromElementId")
    to_element_id: UUID = Field(alias="toElementId")
    label: str | None = None
    connection_type: ConnectionType = Field(alias="connectionType")
    style_json: dict[str, Any] | None = Field(default=None, alias="styleJson")


class PatchCanvasConnectionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str | None = None
    connection_type: ConnectionType | None = Field(default=None, alias="connectionType")
    style_json: dict[str, Any] | None = Field(default=None, alias="styleJson")
