import uuid
from datetime import datetime, timezone

import pytest

from app.models.analysis_run import AnalysisRun
from app.models.analysis_segment import AnalysisSegment
from app.models.generation_job import GenerationJob
from app.models.research_item import ResearchItem
from app.models.usage_event import UsageEvent
from app.models.user import User
from app.repositories.analysis_run_repository import AnalysisRunRepository
from app.repositories.analysis_segment_repository import AnalysisSegmentRepository
from app.repositories.generation_job_repository import GenerationJobRepository
from app.repositories.research_item_repository import ResearchItemRepository
from app.repositories.usage_event_repository import UsageEventRepository


@pytest.mark.asyncio
async def test_research_item_repository_roundtrip(db_session):
    user = User(email="rt1@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=user.id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="t",
        status="COMPLETED",
        original_user_input="q",
        analysis_mode="NOT_APPLICABLE",
        disclaimer="d",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await repo.add(item)
    await db_session.commit()

    fetched = await repo.get_by_id(item.id)
    assert fetched is not None
    assert fetched.id == item.id


@pytest.mark.asyncio
async def test_generation_job_repository_roundtrip(db_session):
    user = User(email="rt2@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    item_repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=user.id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="t",
        status="QUEUED",
        original_user_input="q",
        analysis_mode="NOT_APPLICABLE",
        disclaimer="d",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await item_repo.add(item)

    repo = GenerationJobRepository(db_session)
    job = GenerationJob(
        user_id=user.id,
        research_item_id=item.id,
        job_type="ASK_ANALYSIS",
        status="QUEUED",
        current_step=None,
        retry_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await repo.add(job)
    await db_session.commit()

    fetched = await repo.get_by_id(job.id)
    assert fetched is not None
    assert fetched.id == job.id


@pytest.mark.asyncio
async def test_analysis_run_and_segment_repositories_roundtrip(db_session):
    user = User(email="rt3@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    item_repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=user.id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="t",
        status="QUEUED",
        original_user_input="q",
        analysis_mode="NOT_APPLICABLE",
        disclaimer="d",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await item_repo.add(item)

    run_repo = AnalysisRunRepository(db_session)
    run = AnalysisRun(
        user_id=user.id,
        research_item_id=item.id,
        source_id=None,
        source_scan_id=None,
        generation_job_id=None,
        requested_output_mode="ASK",
        analysis_intent="MARKET_IMPACT",
        requested_research_mode="STANDARD",
        completion_strategy="OPTIMIZE_RESEARCH",
        coverage_mode="FULL_SOURCE",
        focus_question=None,
        status="RUNNING",
        warning_acknowledged=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await run_repo.add(run)

    seg_repo = AnalysisSegmentRepository(db_session)
    seg = AnalysisSegment(
        analysis_run_id=run.id,
        source_segment_id=None,
        segment_index=0,
        title=None,
        start_offset_seconds=None,
        end_offset_seconds=None,
        requested_research_mode="STANDARD",
        actual_research_mode="STANDARD",
        status="COMPLETED",
        downgrade_reason=None,
        can_rerun=False,
        rerun_of_segment_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await seg_repo.add(seg)
    await db_session.commit()

    fetched_run = await run_repo.get_by_id(run.id, with_segments=True)
    assert fetched_run is not None
    assert fetched_run.id == run.id
    assert len(fetched_run.segments) == 1

    fetched_segments = await seg_repo.list_by_run_id(run.id)
    assert [s.id for s in fetched_segments] == [seg.id]


@pytest.mark.asyncio
async def test_usage_event_repository_roundtrip(db_session):
    user = User(email="rt4@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    repo = UsageEventRepository(db_session)
    ev = UsageEvent(
        user_id=user.id,
        research_item_id=None,
        source_id=None,
        event_type="ASK",
        model_provider=None,
        model_name=None,
        input_tokens=None,
        output_tokens=None,
        estimated_allowance_impact_percent=None,
        actual_allowance_impact_percent=None,
        internal_cost_score=None,
        estimated_cost_usd=None,
    )
    await repo.add(ev)
    await db_session.commit()

    fetched = await repo.get_by_id(ev.id)
    assert fetched is not None
    assert fetched.id == ev.id

