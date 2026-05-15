from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

StickyNoteKind = Literal["CLAIM", "RISK", "EVIDENCE", "QUESTION"]


class OnboardingStarterElement(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    element_type: Literal["STICKY_NOTE"] = Field(default="STICKY_NOTE", alias="elementType")
    provenance_kind: Literal["AI_ONBOARDING"] = Field(default="AI_ONBOARDING", alias="provenanceKind")
    kind: StickyNoteKind
    title: str = Field(max_length=80)
    body: str = Field(min_length=1)


class ResearchDirection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str = Field(min_length=1, max_length=80)
    title: str = Field(max_length=70)
    summary: str = Field(min_length=1)
    research_goal: str = Field(min_length=1, alias="researchGoal")
    included_topics: list[str] = Field(default_factory=list, alias="includedTopics")
    excluded_topics: list[str] = Field(default_factory=list, alias="excludedTopics")
    target_entities: list[str] = Field(default_factory=list, alias="targetEntities")
    time_horizon: str | None = Field(default=None, alias="timeHorizon")
    starter_elements: list[OnboardingStarterElement] = Field(
        min_length=3,
        max_length=5,
        alias="starterElements",
    )


class SuggestDirectionsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    description: str = Field(min_length=1, max_length=500)


class SuggestDirectionsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    suggestion_id: UUID = Field(alias="suggestionId")
    directions: list[ResearchDirection] = Field(min_length=3, max_length=3)


class ApplyDirectionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    direction: ResearchDirection
