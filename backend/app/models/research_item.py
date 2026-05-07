from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class ResearchItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "research_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    item_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    original_user_input: Mapped[str] = mapped_column(Text, nullable=False)

    output_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    short_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)

    model_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    requested_research_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completion_strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    coverage_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)

    analysis_depth_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User")

