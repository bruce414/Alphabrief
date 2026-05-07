from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun


class AnalysisSegment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_segments"

    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source_segments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    segment_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)

    start_offset_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    requested_research_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    actual_research_mode: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    downgrade_reason: Mapped[str | None] = mapped_column(String(80), nullable=True)

    analysis_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    key_entities: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    key_topics: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)

    can_rerun: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rerun_of_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("analysis_segments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="segments")

