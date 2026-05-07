from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.source_scan import SourceScan


class SourceSegment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Segment / chunk discovered during cheap scan (DATA_MODEL §4.16)."""

    __tablename__ = "source_segments"

    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_scan_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source_scans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)

    start_offset_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_char_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_char_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    detected_entities: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    detected_topics: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    estimated_complexity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relevance_to_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recommended_research_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    scan: Mapped["SourceScan | None"] = relationship("SourceScan", back_populates="segments")
