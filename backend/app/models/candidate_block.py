from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CandidateStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.canvas_block import CanvasBlock
    from app.models.chat_turn import ChatTurn
    from app.models.project import Project
    from app.models.user import User


class CandidateBlock(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "candidate_blocks"

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

    block_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default=CandidateStatus.PENDING.value, index=True)
    promoted_block_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canvas_blocks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    extraction_model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    chat_turn: Mapped["ChatTurn"] = relationship("ChatTurn")
    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
    promoted_block: Mapped["CanvasBlock | None"] = relationship("CanvasBlock")

