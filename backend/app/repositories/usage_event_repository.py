from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_event import UsageEvent


class UsageEventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, event: UsageEvent) -> UsageEvent:
        self._db.add(event)
        await self._db.flush()
        return event

    async def get_by_id(self, event_id: UUID) -> UsageEvent | None:
        result = await self._db.execute(select(UsageEvent).where(UsageEvent.id == event_id))
        return result.scalar_one_or_none()

