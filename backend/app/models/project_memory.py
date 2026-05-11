from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import MemoryUpdatedBy
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class ProjectMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Explicit, visible project-level accumulated understanding (v0.3)."""

    __tablename__ = "project_memories"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    summary_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    entities_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    themes_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    open_questions_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    conclusions_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    last_compiled_from_activity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    updated_by: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MemoryUpdatedBy.USER.value,
    )

    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
