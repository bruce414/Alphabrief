from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.brief import Brief


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="USER")

    default_output_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ASK",
    )
    default_research_scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RECOMMENDED_CONTEXT",
    )
    default_research_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="STANDARD",
    )
    optimize_research_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    briefs: Mapped[list[Brief]] = relationship(
        "Brief",
        back_populates="user",
    )
