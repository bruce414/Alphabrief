# LEGACY v0.1/v0.2: kept for compatibility. v0.3 brief generation is deferred.
# Do not delete, refactor, or modify in v0.3 prompts.
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brief import Brief
from app.models.brief_source import BriefSource
from app.schemas.brief import BriefCreate


async def create_brief(db: AsyncSession, data: BriefCreate) -> Brief:
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
    await db.commit()
    await db.refresh(brief, attribute_names=["brief_sources"])
    return brief


async def get_brief_by_id(db: AsyncSession, brief_id: UUID) -> Brief | None:
    stmt = (
        select(Brief)
        .where(Brief.id == brief_id)
        .options(selectinload(Brief.brief_sources))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_briefs(db: AsyncSession, limit: int = 20, offset: int = 0) -> list[Brief]:
    stmt = (
        select(Brief)
        .options(selectinload(Brief.brief_sources))
        .order_by(Brief.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.scalars(stmt)
    return list(result.all())
