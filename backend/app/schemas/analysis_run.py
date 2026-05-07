from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CompletionStrategy, CoverageMode, ResearchMode


class AnalysisRunResponse(BaseModel):
    """GET /analysis-runs/{analysisRunId} response (API_SPEC §17)."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    research_item_id: UUID = Field(alias="researchItemId")
    source_id: UUID | None = Field(default=None, alias="sourceId")
    requested_research_mode: ResearchMode = Field(alias="requestedResearchMode")
    completion_strategy: CompletionStrategy = Field(alias="completionStrategy")
    coverage_mode: CoverageMode = Field(alias="coverageMode")
    status: str
    estimated_allowance_impact_percent: float | None = Field(
        default=None, alias="estimatedAllowanceImpactPercent"
    )
    actual_allowance_impact_percent: float | None = Field(
        default=None, alias="actualAllowanceImpactPercent"
    )
    warning_acknowledged: bool = Field(alias="warningAcknowledged")
    current_segment_index: int | None = Field(default=None, alias="currentSegmentIndex")
    segments_total: int = Field(alias="segmentsTotal")

