from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BriefCreate(BaseModel):
    source_url: HttpUrl
    brief_type: str = "BASIC"
    title: str | None = None


class BriefSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_url: str
    source_type: str
    raw_title: str | None
    created_at: datetime


class BriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    title: str | None
    brief_type: str
    status: str
    summary: str | None
    sources: list[BriefSourceResponse] = Field(validation_alias="brief_sources")
    created_at: datetime
    updated_at: datetime
