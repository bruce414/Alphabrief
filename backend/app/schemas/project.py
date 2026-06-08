from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ProjectKind


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=1)
    kind: ProjectKind = Field(default=ProjectKind.COVERAGE)
    description: str | None = None


class PatchProjectRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    description: str | None = None
    archived: bool | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    kind: ProjectKind
    title: str
    description: str | None = None
    archived_at: datetime | None = Field(default=None, alias="archivedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    chat_count: int = Field(alias="chatCount")
    canvas_element_count: int = Field(alias="canvasElementCount")
    source_count: int = Field(alias="sourceCount")
    brief_count: int = Field(alias="briefCount")


class ProjectListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ProjectResponse]

