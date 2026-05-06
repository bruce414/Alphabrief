from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.brief_source import BriefSource
    from app.models.user import User


class Brief(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "briefs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    brief_type: Mapped[str] = mapped_column(String(64), nullable=False, default="BASIC")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="PENDING")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User | None] = relationship(
        "User",
        back_populates="briefs",
    )
    brief_sources: Mapped[list[BriefSource]] = relationship(
        "BriefSource",
        back_populates="brief",
        cascade="all, delete-orphan",
    )
