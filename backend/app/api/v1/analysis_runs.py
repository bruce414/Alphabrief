from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.analysis_run_repository import AnalysisRunRepository
from app.repositories.analysis_segment_repository import AnalysisSegmentRepository
from app.schemas.analysis_run import AnalysisRunResponse
from app.schemas.analysis_segment import AnalysisSegmentListItem, ListAnalysisSegmentsResponse

router = APIRouter(prefix="/analysis-runs", tags=["analysis-runs"])


@router.get("/{analysis_run_id}", response_model=AnalysisRunResponse)
async def get_analysis_run(
    analysis_run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisRunResponse:
    repo = AnalysisRunRepository(db)
    run = await repo.get_by_id(analysis_run_id, with_segments=True)
    if run is None:
        raise AppError(
            error_code="ANALYSIS_RUN_NOT_FOUND",
            message="Analysis run not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if run.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this analysis run",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    segments_total = len(run.segments)
    current_segment_index: int | None = None
    if segments_total > 0:
        incomplete = [s.segment_index for s in run.segments if s.status not in ("COMPLETED",)]
        if incomplete:
            current_segment_index = min(incomplete)
        else:
            current_segment_index = max(s.segment_index for s in run.segments)

    return AnalysisRunResponse(
        id=run.id,
        researchItemId=run.research_item_id,
        sourceId=run.source_id,
        requestedResearchMode=run.requested_research_mode,
        completionStrategy=run.completion_strategy,
        coverageMode=run.coverage_mode,
        status=run.status,
        estimatedAllowanceImpactPercent=(
            float(run.estimated_allowance_impact_percent)
            if run.estimated_allowance_impact_percent is not None
            else None
        ),
        actualAllowanceImpactPercent=(
            float(run.actual_allowance_impact_percent)
            if run.actual_allowance_impact_percent is not None
            else None
        ),
        warningAcknowledged=run.warning_acknowledged,
        currentSegmentIndex=current_segment_index,
        segmentsTotal=segments_total,
    )


@router.get("/{analysis_run_id}/segments", response_model=ListAnalysisSegmentsResponse)
async def list_analysis_segments(
    analysis_run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListAnalysisSegmentsResponse:
    run_repo = AnalysisRunRepository(db)
    run = await run_repo.get_by_id(analysis_run_id, with_segments=False)
    if run is None:
        raise AppError(
            error_code="ANALYSIS_RUN_NOT_FOUND",
            message="Analysis run not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if run.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this analysis run",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if run.status == "QUEUED":
        return ListAnalysisSegmentsResponse(items=[])

    seg_repo = AnalysisSegmentRepository(db)
    segments = await seg_repo.list_by_run_id(analysis_run_id)
    return ListAnalysisSegmentsResponse(
        items=[
            AnalysisSegmentListItem(
                id=s.id,
                segmentIndex=s.segment_index,
                title=s.title,
                startOffsetSeconds=s.start_offset_seconds,
                endOffsetSeconds=s.end_offset_seconds,
                requestedResearchMode=s.requested_research_mode,
                actualResearchMode=s.actual_research_mode,
                status=s.status,
                downgradeReason=s.downgrade_reason,
                canRerun=s.can_rerun,
            )
            for s in segments
        ]
    )

