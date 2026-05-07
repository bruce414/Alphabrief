from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, desc, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_item import ResearchItem


class ResearchItemRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, item: ResearchItem) -> ResearchItem:
        self._db.add(item)
        await self._db.flush()
        return item

    async def get_by_id(self, item_id: UUID) -> ResearchItem | None:
        result = await self._db.execute(select(ResearchItem).where(ResearchItem.id == item_id))
        return result.scalar_one_or_none()

    async def list_by_user_cursor(
        self,
        *,
        user_id: UUID,
        limit: int,
        cursor_id: UUID | None = None,
    ) -> tuple[list[ResearchItem], UUID | None]:
        stmt: Select[tuple[ResearchItem]] = (
            select(ResearchItem)
            .where(ResearchItem.user_id == user_id)
            .order_by(desc(ResearchItem.created_at), desc(ResearchItem.id))
            .limit(limit + 1)
        )

        if cursor_id is not None:
            cursor_row = await self.get_by_id(cursor_id)
            if cursor_row is not None and cursor_row.user_id == user_id:
                stmt = stmt.where(
                    tuple_(ResearchItem.created_at, ResearchItem.id)
                    < tuple_(cursor_row.created_at, cursor_row.id)
                )

        result = await self._db.execute(stmt)
        rows = list(result.scalars().all())
        next_cursor: UUID | None = None
        if len(rows) > limit:
            next_cursor = rows[limit - 1].id
            rows = rows[:limit]
        return rows, next_cursor

