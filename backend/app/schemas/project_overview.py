from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OverviewStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_nodes: int = Field(alias="totalNodes")
    total_sources: int = Field(alias="totalSources")
    open_questions_count: int = Field(default=0, alias="openQuestionsCount")
    unsupported_claims_count: int = Field(default=0, alias="unsupportedClaimsCount")
    updates_available_count: int = Field(default=0, alias="updatesAvailableCount")
    last_checked_at: datetime | None = Field(default=None, alias="lastCheckedAt")


class OverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    research_goal: str | None = Field(default=None, alias="researchGoal")
    research_type: str | None = Field(default=None, alias="researchType")
    included_topics: list[str] = Field(default_factory=list, alias="includedTopics")
    excluded_topics: list[str] = Field(default_factory=list, alias="excludedTopics")
    target_entities: list[str] = Field(default_factory=list, alias="targetEntities")
    time_horizon: str | None = Field(default=None, alias="timeHorizon")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    status: OverviewStatusResponse


class PatchOverviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    research_goal: str | None = Field(default=None, alias="researchGoal")
    research_type: str | None = Field(default=None, alias="researchType")
    included_topics: list[str] | None = Field(default=None, alias="includedTopics")
    excluded_topics: list[str] | None = Field(default=None, alias="excludedTopics")
    target_entities: list[str] | None = Field(default=None, alias="targetEntities")
    time_horizon: str | None = Field(default=None, alias="timeHorizon")
