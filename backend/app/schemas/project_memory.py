from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectMemoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    project_id: UUID = Field(alias="projectId")
    summary_markdown: str | None = Field(default=None, alias="summaryMarkdown")
    entities: list[Any]
    themes: list[Any]
    open_questions: list[Any] = Field(alias="openQuestions")
    conclusions: list[Any]
    updated_at: datetime = Field(alias="updatedAt")


class PatchProjectMemoryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary_markdown: str | None = Field(default=None, alias="summaryMarkdown")
    entities: list[Any] | None = None
    themes: list[Any] | None = None
    open_questions: list[Any] | None = Field(default=None, alias="openQuestions")
    conclusions: list[Any] | None = None


class RefreshProjectMemoryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: Literal["RECENT_ACTIVITY"] = "RECENT_ACTIVITY"
    max_activity_items: int = Field(default=30, alias="maxActivityItems", ge=1)


class RefreshProjectMemoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    memory_refresh_job_id: UUID = Field(alias="memoryRefreshJobId")
    status: Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "NO_ACTIVITY"]
