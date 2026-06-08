from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_fetch_policy import SourceFetchPolicy


class SourceFetchPolicyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_domain(self, domain: str) -> SourceFetchPolicy | None:
        stmt = select(SourceFetchPolicy).where(SourceFetchPolicy.domain == domain)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_robots(
        self,
        *,
        domain: str,
        robots_txt_url: str,
        robots_txt_content: str | None,
        robots_status: int | None,
        fetched_at: datetime | None,
        expires_at: datetime | None,
        metadata: dict,
    ) -> SourceFetchPolicy:
        existing = await self.get_by_domain(domain)
        if existing is None:
            existing = SourceFetchPolicy(domain=domain)
            self._db.add(existing)

        existing.robots_txt_url = robots_txt_url
        existing.robots_txt_content = robots_txt_content
        existing.robots_status = robots_status
        existing.robots_fetched_at = fetched_at
        existing.robots_expires_at = expires_at
        existing.metadata_ = metadata or {}

        await self._db.commit()
        await self._db.refresh(existing)
        return existing

