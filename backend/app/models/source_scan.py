from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.source_segment import SourceSegment


class SourceScan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cheap pre-analysis scan result for an external source (DATA_MODEL §4.15)."""

    __tablename__ = "source_scans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requested_output_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    analysis_intent: Mapped[str] = mapped_column(String(50), nullable=False)
    requested_research_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    coverage_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    focus_question: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_complexity: Mapped[str] = mapped_column(String(50), nullable=False)
    estimate_confidence: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_allowance_impact_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    requires_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    warning_level: Mapped[str] = mapped_column(String(50), nullable=False)

    recommended_research_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    recommended_completion_strategy: Mapped[str] = mapped_column(String(50), nullable=False)

    detected_topics: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    detected_entities: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    segments: Mapped[list["SourceSegment"]] = relationship(
        "SourceSegment",
        back_populates="scan",
        cascade="all, delete-orphan",
        order_by="SourceSegment.segment_index",
    )
