from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SourceFetchPolicy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "source_fetch_policies"

    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    robots_txt_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    robots_txt_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    robots_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    robots_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    robots_status: Mapped[int | None] = mapped_column(Integer, nullable=True)

    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)

