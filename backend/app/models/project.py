from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    included_topics: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    excluded_topics: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    target_entities: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    time_horizon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updates_available_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship("User", back_populates="projects")

    __table_args__ = (
        Index(
            "uq_projects_one_catchall_per_user",
            "user_id",
            unique=True,
            postgresql_where=(kind == "CATCHALL"),
        ),
    )

