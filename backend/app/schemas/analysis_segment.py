from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ResearchMode


class AnalysisSegmentListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    segment_index: int = Field(alias="segmentIndex")
    title: str | None = None
    start_offset_seconds: int | None = Field(default=None, alias="startOffsetSeconds")
    end_offset_seconds: int | None = Field(default=None, alias="endOffsetSeconds")
    requested_research_mode: ResearchMode = Field(alias="requestedResearchMode")
    actual_research_mode: ResearchMode = Field(alias="actualResearchMode")
    status: str
    downgrade_reason: str | None = Field(default=None, alias="downgradeReason")
    can_rerun: bool = Field(alias="canRerun")


class ListAnalysisSegmentsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[AnalysisSegmentListItem]

