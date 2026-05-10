from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateSourceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_type: Literal["ARTICLE_URL", "YOUTUBE_URL", "FILING_URL", "AUTO_DETECT"] = Field(
        alias="sourceType"
    )
    input: str = Field(min_length=1)
    project_id: UUID | None = Field(default=None, alias="projectId")


class SourceCreateResponse(BaseModel):
    """Subset returned by POST /sources (API_SPEC §4)."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    source_id: UUID = Field(alias="sourceId")
    source_type: str = Field(alias="sourceType")
    source_access_method: str = Field(alias="sourceAccessMethod")
    source_access_status: str = Field(alias="sourceAccessStatus")
    normalized_url: str | None = Field(default=None, alias="normalizedUrl")
    canonical_url: str | None = Field(default=None, alias="canonicalUrl")
    title: str | None = None
    publisher: str | None = None
    extracted_text_word_count: int | None = Field(default=None, alias="extractedTextWordCount")
    extraction_confidence: str | None = Field(default=None, alias="extractionConfidence")


class SourceDetailResponse(BaseModel):
    """Full row for GET /sources/{sourceId} (owner only)."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID
    source_type: str = Field(alias="sourceType")
    source_access_method: str = Field(alias="sourceAccessMethod")
    source_access_status: str = Field(alias="sourceAccessStatus")
    original_input: str = Field(alias="originalInput")
    normalized_url: str | None = Field(default=None, alias="normalizedUrl")
    canonical_url: str | None = Field(default=None, alias="canonicalUrl")
    title: str | None = None
    publisher: str | None = None
    author: str | None = None
    published_at: datetime | None = Field(default=None, alias="publishedAt")
    extracted_text: str | None = Field(default=None, alias="extractedText")
    extracted_text_word_count: int | None = Field(default=None, alias="extractedTextWordCount")
    extraction_confidence: str | None = Field(default=None, alias="extractionConfidence")
    extraction_error: str | None = Field(default=None, alias="extractionError")
    raw_text_retention: str = Field(alias="rawTextRetention")
    content_hash: str | None = Field(default=None, alias="contentHash")
    payload_metadata: dict[str, Any] = Field(alias="metadata")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
