from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generation_job import GenerationJob


class GenerationJobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, job: GenerationJob) -> GenerationJob:
        self._db.add(job)
        await self._db.flush()
        return job

    async def get_by_id(self, job_id: UUID) -> GenerationJob | None:
        result = await self._db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
        return result.scalar_one_or_none()

