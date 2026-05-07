from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ResearchScopesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    research_scopes: list[str] = Field(alias="researchScopes")
    research_modes: list[str] = Field(alias="researchModes")
    completion_strategies: list[str] = Field(alias="completionStrategies")
    coverage_modes: list[str] = Field(alias="coverageModes")
    analysis_intents: list[str] = Field(alias="analysisIntents")

