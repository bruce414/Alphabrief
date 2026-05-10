from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.canvas import Canvas
    from app.models.canvas_element import CanvasElement
    from app.models.project import Project
    from app.models.user import User


class CanvasConnection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Edge between two Canvas elements (mind-map / relationship line)."""

    __tablename__ = "canvas_connections"

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

    from_element_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canvas_elements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_element_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canvas_elements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    label: Mapped[str | None] = mapped_column(Text, nullable=True)
    connection_type: Mapped[str] = mapped_column(String(40), nullable=False)
    style_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    canvas: Mapped["Canvas"] = relationship("Canvas")
    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
    from_element: Mapped["CanvasElement"] = relationship(
        "CanvasElement", foreign_keys=[from_element_id]
    )
    to_element: Mapped["CanvasElement"] = relationship(
        "CanvasElement", foreign_keys=[to_element_id]
    )
