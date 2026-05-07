from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import AnalysisMode, CompletionStrategy, CoverageMode, ResearchMode


class ResearchItemListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    item_type: str = Field(alias="itemType")
    title: str
    short_summary: str | None = Field(default=None, alias="shortSummary")
    status: str
    analysis_mode: AnalysisMode = Field(alias="analysisMode")
    created_at: datetime = Field(alias="createdAt")


class ListResearchItemsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[ResearchItemListItem]
    next_cursor: UUID | None = Field(default=None, alias="nextCursor")


class ResearchItemDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    user_id: UUID = Field(alias="userId")
    source_id: UUID | None = Field(default=None, alias="sourceId")

    item_type: str = Field(alias="itemType")
    title: str
    status: str

    original_user_input: str = Field(alias="originalUserInput")

    output_markdown: str | None = Field(default=None, alias="outputMarkdown")
    output_json: dict[str, Any] | None = Field(default=None, alias="outputJson")

    short_summary: str | None = Field(default=None, alias="shortSummary")
    confidence_label: str | None = Field(default=None, alias="confidenceLabel")
    confidence_explanation: str | None = Field(default=None, alias="confidenceExplanation")

    analysis_mode: AnalysisMode = Field(alias="analysisMode")
    disclaimer: str

    model_provider: str | None = Field(default=None, alias="modelProvider")
    model_name: str | None = Field(default=None, alias="modelName")
    prompt_version: str | None = Field(default=None, alias="promptVersion")

    requested_research_mode: ResearchMode | None = Field(
        default=None, alias="requestedResearchMode"
    )
    completion_strategy: CompletionStrategy | None = Field(
        default=None, alias="completionStrategy"
    )
    coverage_mode: CoverageMode | None = Field(default=None, alias="coverageMode")

    analysis_depth_summary: dict[str, Any] | None = Field(
        default=None, alias="analysisDepthSummary"
    )

    generated_at: datetime | None = Field(default=None, alias="generatedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

