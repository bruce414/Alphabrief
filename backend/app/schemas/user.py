from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ResearchMode, ResearchScope


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    email: str
    display_name: str | None = Field(default=None, alias="displayName")
    default_output_mode: str = Field(alias="defaultOutputMode")
    default_research_scope: ResearchScope = Field(alias="defaultResearchScope")
    default_research_mode: ResearchMode = Field(alias="defaultResearchMode")
    optimize_research_default: bool = Field(alias="optimizeResearchDefault")
    created_at: datetime = Field(alias="createdAt")


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, alias="displayName", max_length=120)
    default_output_mode: str | None = Field(default=None, alias="defaultOutputMode")
    default_research_scope: ResearchScope | None = Field(
        default=None, alias="defaultResearchScope"
    )
    default_research_mode: ResearchMode | None = Field(default=None, alias="defaultResearchMode")
    optimize_research_default: bool | None = Field(default=None, alias="optimizeResearchDefault")

