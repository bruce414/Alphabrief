from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.brief import Brief


class BriefSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brief_sources"

    brief_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("briefs.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="URL")
    raw_title: Mapped[str | None] = mapped_column(String(512), nullable=True)

    brief: Mapped[Brief] = relationship(
        "Brief",
        back_populates="brief_sources",
    )
