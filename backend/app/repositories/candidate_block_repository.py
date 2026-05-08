from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CandidateStatus
from app.models.candidate_block import CandidateBlock


class CandidateBlockRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, candidate: CandidateBlock) -> CandidateBlock:
        self._db.add(candidate)
        await self._db.commit()
        await self._db.refresh(candidate)
        return candidate

    async def update(self, candidate: CandidateBlock) -> CandidateBlock:
        self._db.add(candidate)
        await self._db.commit()
        await self._db.refresh(candidate)
        return candidate

    async def get_by_id(self, candidate_id: UUID) -> CandidateBlock | None:
        result = await self._db.execute(select(CandidateBlock).where(CandidateBlock.id == candidate_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, *, candidate_id: UUID, user_id: UUID) -> CandidateBlock | None:
        stmt: Select[tuple[CandidateBlock]] = select(CandidateBlock).where(
            CandidateBlock.id == candidate_id,
            CandidateBlock.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_turn(
        self,
        *,
        chat_turn_id: UUID,
        include_all: bool,
    ) -> list[CandidateBlock]:
        stmt: Select[tuple[CandidateBlock]] = select(CandidateBlock).where(CandidateBlock.chat_turn_id == chat_turn_id)
        if not include_all:
            stmt = stmt.where(CandidateBlock.status == CandidateStatus.PENDING.value)
        stmt = stmt.order_by(CandidateBlock.created_at.asc(), CandidateBlock.id.asc())
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

