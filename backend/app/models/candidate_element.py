from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CandidateStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.canvas_element import CanvasElement
    from app.models.chat_turn import ChatTurn
    from app.models.project import Project
    from app.models.user import User


class CandidateElement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI-suggested Canvas element awaiting user promote/dismiss (v0.3)."""

    __tablename__ = "candidate_elements"

    chat_turn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_turns.id", ondelete="CASCADE"),
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

    suggested_element_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=CandidateStatus.PENDING.value,
        index=True,
    )
    promoted_element_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canvas_elements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    extraction_model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    chat_turn: Mapped["ChatTurn"] = relationship("ChatTurn")
    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
    promoted_element: Mapped["CanvasElement | None"] = relationship("CanvasElement")
