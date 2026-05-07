from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


RequestedOutputMode = Literal["ASK", "BRIEF"]
AnalysisIntent = Literal[
    "QUICK_SUMMARY",
    "MARKET_IMPACT",
    "COMPANY_ANALYSIS",
    "LEARNING_MODE",
    "STRUCTURED_BRIEF",
]
ResearchMode = Literal["QUICK", "STANDARD", "DEEP"]
CoverageMode = Literal[
    "FULL_SOURCE",
    "SELECTED_TOPICS",
    "SELECTED_ENTITIES",
    "CUSTOM_QUESTION",
]
SourceComplexity = Literal["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
EstimateConfidence = Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
WarningLevel = Literal["NONE", "INLINE", "HIGH", "VERY_HIGH"]
CompletionStrategy = Literal["STRICT_REQUESTED_MODE", "OPTIMIZE_RESEARCH"]


class RunSourceScanRequest(BaseModel):
    """POST /sources/{sourceId}/scan request body (API_SPEC §17)."""

    model_config = ConfigDict(populate_by_name=True)

    requested_output_mode: RequestedOutputMode = Field(alias="requestedOutputMode")
    analysis_intent: AnalysisIntent = Field(alias="analysisIntent")
    research_mode: ResearchMode = Field(alias="researchMode")
    coverage_mode: CoverageMode = Field(alias="coverageMode")
    focus_question: str | None = Field(default=None, alias="focusQuestion")


class DetectedEntity(BaseModel):
    """Detected company/ticker/macro entity surfaced from the scan."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    ticker: str | None = None
    type: str


class SourceSegmentSummary(BaseModel):
    """Per-segment summary inlined in the scan response (API_SPEC §17)."""

    model_config = ConfigDict(populate_by_name=True)

    segment_id: UUID = Field(alias="segmentId")
    segment_index: int = Field(alias="segmentIndex")
    start_offset_seconds: int | None = Field(default=None, alias="startOffsetSeconds")
    end_offset_seconds: int | None = Field(default=None, alias="endOffsetSeconds")
    start_char_offset: int | None = Field(default=None, alias="startCharOffset")
    end_char_offset: int | None = Field(default=None, alias="endCharOffset")
    title: str | None = None
    topic_summary: str | None = Field(default=None, alias="topicSummary")
    estimated_complexity: SourceComplexity | None = Field(
        default=None, alias="estimatedComplexity"
    )
    recommended_depth: ResearchMode | None = Field(
        default=None, alias="recommendedDepth"
    )


class RunSourceScanResponse(BaseModel):
    """POST /sources/{sourceId}/scan response (API_SPEC §17)."""

    model_config = ConfigDict(populate_by_name=True)

    source_id: UUID = Field(alias="sourceId")
    scan_id: UUID = Field(alias="scanId")
    source_complexity: SourceComplexity = Field(alias="sourceComplexity")
    estimate_confidence: EstimateConfidence = Field(alias="estimateConfidence")
    estimated_allowance_impact_percent: float = Field(
        alias="estimatedAllowanceImpactPercent"
    )
    requires_warning: bool = Field(alias="requiresWarning")
    warning_level: WarningLevel = Field(alias="warningLevel")
    recommended_research_mode: ResearchMode = Field(alias="recommendedResearchMode")
    recommended_completion_strategy: CompletionStrategy = Field(
        alias="recommendedCompletionStrategy"
    )
    detected_topics: list[str] = Field(alias="detectedTopics")
    detected_entities: list[DetectedEntity] = Field(alias="detectedEntities")
    segments: list[SourceSegmentSummary]
