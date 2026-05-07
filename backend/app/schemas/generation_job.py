from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GenerationJobResponse(BaseModel):
    """GET /jobs/{jobId} response (API_SPEC §9)."""

    model_config = ConfigDict(populate_by_name=True)

    job_id: UUID = Field(alias="jobId")
    research_item_id: UUID | None = Field(default=None, alias="researchItemId")
    job_type: str = Field(alias="jobType")
    status: str
    current_step: str | None = Field(default=None, alias="currentStep")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")

