from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.brief import Brief
from app.models.brief_source import BriefSource
from app.schemas.brief import BriefCreate


def create_brief(db: Session, data: BriefCreate) -> Brief:
    brief = Brief(
        title=data.title,
        brief_type=data.brief_type,
        status="PENDING",
        summary=None,
        user_id=None,
    )
    brief.brief_sources.append(
        BriefSource(
            source_url=str(data.source_url),
            source_type="URL",
            raw_title=None,
        )
    )
    db.add(brief)
    db.commit()
    db.refresh(brief, attribute_names=["brief_sources"])
    return brief


def get_brief_by_id(db: Session, brief_id: UUID) -> Brief | None:
    stmt = (
        select(Brief)
        .where(Brief.id == brief_id)
        .options(selectinload(Brief.brief_sources))
    )
    return db.execute(stmt).scalar_one_or_none()


def list_briefs(db: Session, limit: int = 20, offset: int = 0) -> list[Brief]:
    stmt = (
        select(Brief)
        .options(selectinload(Brief.brief_sources))
        .order_by(Brief.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())
