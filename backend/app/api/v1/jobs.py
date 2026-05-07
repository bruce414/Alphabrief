from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.generation_job_repository import GenerationJobRepository
from app.repositories.research_item_repository import ResearchItemRepository
from app.schemas.generation_job import GenerationJobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=GenerationJobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerationJobResponse:
    job_repo = GenerationJobRepository(db)
    job = await job_repo.get_by_id(job_id)
    if job is None:
        raise AppError(
            error_code="JOB_NOT_FOUND",
            message="Job not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if job.research_item_id is not None:
        item_repo = ResearchItemRepository(db)
        item = await item_repo.get_by_id(job.research_item_id)
        if item is None:
            raise AppError(
                error_code="RESEARCH_ITEM_NOT_FOUND",
                message="Research item not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if item.user_id != current_user.id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this job",
                status_code=status.HTTP_403_FORBIDDEN,
            )
    else:
        if job.user_id != current_user.id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this job",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return GenerationJobResponse(
        jobId=job.id,
        researchItemId=job.research_item_id,
        jobType=job.job_type,
        status=job.status,
        currentStep=job.current_step,
        errorCode=job.error_code,
        errorMessage=job.error_message,
    )

