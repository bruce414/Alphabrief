from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CanvasResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    project_id: UUID = Field(alias="projectId")
    title: str
    viewport_json: dict[str, Any] = Field(alias="viewportJson")
    updated_at: datetime = Field(alias="updatedAt")
