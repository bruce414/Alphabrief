from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.chat_turn import ChatTurn
    from app.models.project import Project
    from app.models.source import Source
    from app.models.user import User


class CanvasBlock(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "canvas_blocks"

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

    block_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    position_index: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False, index=True)

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
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
    provenance_chat_turn: Mapped["ChatTurn | None"] = relationship("ChatTurn")
    provenance_source: Mapped["Source | None"] = relationship("Source")

