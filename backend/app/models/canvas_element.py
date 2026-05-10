from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.canvas import Canvas
    from app.models.chat_turn import ChatTurn
    from app.models.project import Project
    from app.models.source import Source
    from app.models.user import User


class CanvasElement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Atomic visual element on a freeform Canvas (v0.3 replacement for CanvasBlock)."""

    __tablename__ = "canvas_elements"

    canvas_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canvases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    element_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    x: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    y: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    width: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    height: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    style_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    provenance_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    provenance_chat_turn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_turns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    provenance_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    confidence_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    edited_by_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    canvas: Mapped["Canvas"] = relationship("Canvas")
    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
    provenance_chat_turn: Mapped["ChatTurn | None"] = relationship("ChatTurn")
    provenance_source: Mapped["Source | None"] = relationship("Source")
