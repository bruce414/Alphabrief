from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canvas_block import CanvasBlock


class CanvasBlockRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, block: CanvasBlock) -> CanvasBlock:
        self._db.add(block)
        await self._db.commit()
        await self._db.refresh(block)
        return block

    async def update(self, block: CanvasBlock) -> CanvasBlock:
        self._db.add(block)
        await self._db.commit()
        await self._db.refresh(block)
        return block

    async def delete(self, block: CanvasBlock) -> None:
        await self._db.delete(block)
        await self._db.commit()

    async def get_by_id(self, block_id: UUID) -> CanvasBlock | None:
        result = await self._db.execute(select(CanvasBlock).where(CanvasBlock.id == block_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, *, block_id: UUID, user_id: UUID) -> CanvasBlock | None:
        stmt: Select[tuple[CanvasBlock]] = select(CanvasBlock).where(
            CanvasBlock.id == block_id,
            CanvasBlock.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_project(
        self,
        *,
        project_id: UUID,
        include_archived: bool,
    ) -> list[CanvasBlock]:
        stmt: Select[tuple[CanvasBlock]] = select(CanvasBlock).where(CanvasBlock.project_id == project_id)
        if not include_archived:
            stmt = stmt.where(CanvasBlock.archived_at.is_(None))
        stmt = stmt.order_by(CanvasBlock.position_index.asc(), CanvasBlock.created_at.asc(), CanvasBlock.id.asc())
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_active_for_project(self, *, project_id: UUID) -> list[CanvasBlock]:
        stmt: Select[tuple[CanvasBlock]] = (
            select(CanvasBlock)
            .where(CanvasBlock.project_id == project_id, CanvasBlock.archived_at.is_(None))
            .order_by(CanvasBlock.position_index.asc(), CanvasBlock.created_at.asc(), CanvasBlock.id.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_next_active_after(
        self,
        *,
        project_id: UUID,
        position_index: Decimal,
    ) -> CanvasBlock | None:
        stmt: Select[tuple[CanvasBlock]] = (
            select(CanvasBlock)
            .where(
                CanvasBlock.project_id == project_id,
                CanvasBlock.archived_at.is_(None),
                CanvasBlock.position_index > position_index,
            )
            .order_by(CanvasBlock.position_index.asc(), CanvasBlock.id.asc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_max_active_position(self, *, project_id: UUID) -> Decimal | None:
        stmt = select(func.max(CanvasBlock.position_index)).where(
            CanvasBlock.project_id == project_id,
            CanvasBlock.archived_at.is_(None),
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_active_for_project(self, *, project_id: UUID) -> int:
        stmt = select(func.count()).select_from(CanvasBlock).where(
            CanvasBlock.project_id == project_id,
            CanvasBlock.archived_at.is_(None),
        )
        result = await self._db.execute(stmt)
        return int(result.scalar_one())

    async def rebalance_active_positions(self, *, project_id: UUID) -> None:
        blocks = await self.list_active_for_project(project_id=project_id)
        for idx, b in enumerate(blocks, start=1):
            b.position_index = Decimal(idx)
            self._db.add(b)
        await self._db.commit()

    async def hard_delete_for_project(self, *, project_id: UUID) -> None:
        # Test helper convenience (not used by API).
        await self._db.execute(delete(CanvasBlock).where(CanvasBlock.project_id == project_id))
        await self._db.commit()

