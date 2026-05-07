"""HTTP-facing orchestration for research item creation (PR #8b)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AnalysisMode
from app.core.errors import AppError
from app.models.analysis_run import AnalysisRun
from app.models.generation_job import GenerationJob
from app.models.research_item import ResearchItem
from app.models.source_scan import SourceScan
from app.models.user import User
from app.repositories.source_repository import SourceRepository
from app.schemas.research_item import (
    ResearchItemFromSourceRequest,
    ResearchItemFromSourceResponse,
)
from app.services.warning_gate import validate_warning_acknowledgement

DEFAULT_RESEARCH_DISCLAIMER = (
    "AlphaBrief provides informational research outputs only and does not offer "
    "investment advice tailored to any individual."
)


async def create_research_item_from_source(
    db: AsyncSession,
    *,
    body: ResearchItemFromSourceRequest,
    user: User,
) -> ResearchItemFromSourceResponse:
    repo = SourceRepository(db)
    source = await repo.get_by_id(body.source_id)
    if source is None:
        raise AppError(
            error_code="SOURCE_NOT_FOUND",
            message="Source not found",
            status_code=404,
        )
    if source.user_id != user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this source",
            status_code=403,
        )

    scan = await db.scalar(
        select(SourceScan)
        .where(SourceScan.source_id == source.id)
        .order_by(desc(SourceScan.created_at))
        .limit(1)
    )
    if scan is None:
        raise AppError(
            error_code="SCAN_REQUIRED_FIRST",
            message="Run a source scan before starting analysis.",
            status_code=400,
        )

    validate_warning_acknowledgement(
        scan,
        requested_research_mode=body.research_mode,
        acknowledged_high_usage_warning=body.acknowledged_high_usage_warning,
    )

    if source.source_access_status == "FULL_TEXT_EXTRACTED":
        analysis_mode = AnalysisMode.SOURCE_BRIEF
    elif source.source_access_status == "METADATA_ONLY":
        analysis_mode = AnalysisMode.CONTEXT_BRIEF
    else:
        raise AppError(
            error_code="SOURCE_NOT_ANALYZABLE",
            message="This source cannot be analyzed in its current access state.",
            status_code=400,
        )

    item_id = uuid.uuid4()
    job_id = uuid.uuid4()
    run_id = uuid.uuid4()

    opt_ctx = {
        "selectedSegmentIds": [str(x) for x in body.selected_segment_ids],
        "selectedEntityIds": [str(x) for x in body.selected_entity_ids],
        "researchScope": body.research_scope.value,
    }

    item = ResearchItem(
        id=item_id,
        user_id=user.id,
        source_id=source.id,
        item_type="SOURCE_ANALYSIS",
        title=(source.title or "Source analysis"),
        status="QUEUED",
        original_user_input=body.focus_question or "Analyze this source.",
        analysis_mode=analysis_mode.value,
        disclaimer=DEFAULT_RESEARCH_DISCLAIMER,
        requested_research_mode=body.research_mode.value,
        completion_strategy=body.completion_strategy.value,
        coverage_mode=body.coverage_mode.value,
        analysis_depth_summary={"_optimizationContext": opt_ctx},
    )
    job = GenerationJob(
        id=job_id,
        user_id=user.id,
        research_item_id=item_id,
        job_type="ADAPTIVE_SOURCE_ANALYSIS",
        status="QUEUED",
    )
    run = AnalysisRun(
        id=run_id,
        user_id=user.id,
        research_item_id=item_id,
        source_id=source.id,
        source_scan_id=scan.id,
        generation_job_id=job_id,
        requested_output_mode=body.requested_output_mode,
        analysis_intent=body.analysis_intent.value,
        requested_research_mode=body.research_mode.value,
        completion_strategy=body.completion_strategy.value,
        coverage_mode=body.coverage_mode.value,
        focus_question=body.focus_question,
        status="QUEUED",
        estimated_allowance_impact_percent=Decimal(scan.estimated_allowance_impact_percent),
        warning_acknowledged=body.acknowledged_high_usage_warning,
    )

    db.add(item)
    await db.flush()
    db.add(job)
    await db.flush()
    db.add(run)
    await db.commit()

    est = float(scan.estimated_allowance_impact_percent)

    return ResearchItemFromSourceResponse(
        research_item_id=item_id,
        analysis_run_id=run_id,
        job_id=job_id,
        status="QUEUED",
        analysis_mode=analysis_mode,
        research_mode=body.research_mode,
        completion_strategy=body.completion_strategy,
        estimated_allowance_impact_percent=est,
        requires_pre_analysis_warning=scan.requires_warning,
    )
