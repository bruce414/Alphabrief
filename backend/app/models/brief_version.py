# LEGACY v0.1/v0.2: kept for compatibility. v0.3 brief generation is deferred.
# Do not delete, refactor, or modify in v0.3 prompts.
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.brief import Brief
    from app.models.canvas_snapshot import CanvasSnapshot
    from app.models.project import Project
    from app.models.user import User


class BriefVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brief_versions"

    brief_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("briefs.id", ondelete="CASCADE"),
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

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    canvas_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canvas_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="QUEUED")
    content_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    summary_of_changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_from_block_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)

    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    brief: Mapped["Brief"] = relationship(
        "Brief",
        foreign_keys=[brief_id],
    )
    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
    canvas_snapshot: Mapped["CanvasSnapshot"] = relationship("CanvasSnapshot")

