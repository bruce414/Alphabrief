from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class Source(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sources"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_access_method: Mapped[str] = mapped_column(String(50), nullable=False)
    source_access_status: Mapped[str] = mapped_column(String(50), nullable=False)

    original_input: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    file_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    publisher: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text_word_count: Mapped[int | None] = mapped_column(nullable=True)
    extraction_confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_text_retention: Mapped[str] = mapped_column(String(50), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    source_complexity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    segment_count: Mapped[int | None] = mapped_column(nullable=True)
    scan_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="sources")
