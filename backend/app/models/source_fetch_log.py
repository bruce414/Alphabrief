from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class SourceFetchLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "source_fetch_log"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    robots_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    action_taken: Mapped[str] = mapped_column(String(50), nullable=False)
    denied_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)

    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

