from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.brief_source import BriefSource
    from app.models.brief_version import BriefVersion
    from app.models.project import Project
    from app.models.user import User


class Brief(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "briefs"

    # NOTE: This table started as a v0.1 "URL brief" concept. For v0.3 we extend it
    # to support workspace projects + versioned briefs while keeping legacy endpoints working.
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    brief_type: Mapped[str] = mapped_column(String(64), nullable=False, default="BASIC")
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "brief_versions.id",
            name="fk_briefs_current_version_id_brief_versions",
            ondelete="SET NULL",
            use_alter=True,
        ),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="ACTIVE")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    user: Mapped[User | None] = relationship(
        "User",
        back_populates="briefs",
    )
    project: Mapped["Project | None"] = relationship("Project")
    brief_sources: Mapped[list[BriefSource]] = relationship(
        "BriefSource",
        back_populates="brief",
        cascade="all, delete-orphan",
    )
    current_version: Mapped["BriefVersion | None"] = relationship(
        "BriefVersion",
        foreign_keys=[current_version_id],
    )
