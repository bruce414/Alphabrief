from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analysis_segment import AnalysisSegment
    from app.models.user import User


class AnalysisRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_runs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    research_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_scan_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source_scans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    generation_job_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    requested_output_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    analysis_intent: Mapped[str] = mapped_column(String(50), nullable=False)
    requested_research_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    completion_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    coverage_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    focus_question: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    estimated_allowance_impact_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    actual_allowance_impact_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    warning_acknowledged: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    allowance_before_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    allowance_after_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User")
    segments: Mapped[list["AnalysisSegment"]] = relationship(
        "AnalysisSegment",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AnalysisSegment.segment_index",
    )

