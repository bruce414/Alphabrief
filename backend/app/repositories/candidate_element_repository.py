from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CandidateStatus
from app.models.candidate_element import CandidateElement


class CandidateElementRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, candidate: CandidateElement) -> CandidateElement:
        self._db.add(candidate)
        await self._db.commit()
        await self._db.refresh(candidate)
        return candidate

    async def update(self, candidate: CandidateElement) -> CandidateElement:
        self._db.add(candidate)
        await self._db.commit()
        await self._db.refresh(candidate)
        return candidate

    async def get_by_id(self, candidate_id: UUID) -> CandidateElement | None:
        result = await self._db.execute(select(CandidateElement).where(CandidateElement.id == candidate_id))
        return result.scalar_one_or_none()

    async def list_for_turn(
        self,
        *,
        chat_turn_id: UUID,
        include_all: bool,
    ) -> list[CandidateElement]:
        stmt: Select[tuple[CandidateElement]] = select(CandidateElement).where(
            CandidateElement.chat_turn_id == chat_turn_id
        )
        if not include_all:
            stmt = stmt.where(CandidateElement.status == CandidateStatus.PENDING.value)
        stmt = stmt.order_by(CandidateElement.created_at.asc(), CandidateElement.id.asc())
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
