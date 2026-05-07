import uuid
from datetime import datetime, timezone

import pytest

from app.models.analysis_run import AnalysisRun
from app.models.analysis_segment import AnalysisSegment
from app.models.research_item import ResearchItem
from app.repositories.analysis_run_repository import AnalysisRunRepository
from app.repositories.analysis_segment_repository import AnalysisSegmentRepository
from app.repositories.research_item_repository import ResearchItemRepository


async def _register(client, email: str) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_get_analysis_run_owner_check_and_404(client, db_session):
    await _register(client, "ar1@example.com")
    missing = uuid.uuid4()
    resp = await client.get(f"/api/v1/analysis-runs/{missing}")
    assert resp.status_code == 404

    me = (await client.get("/api/v1/me")).json()
    owner_id = uuid.UUID(me["id"])

    await client.post("/api/v1/auth/logout")
    await _register(client, "ar2@example.com")
    other = (await client.get("/api/v1/me")).json()
    other_id = uuid.UUID(other["id"])

    item_repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=other_id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="x",
        status="COMPLETED",
        original_user_input="q",
        analysis_mode="NOT_APPLICABLE",
        disclaimer="d",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await item_repo.add(item)

    run_repo = AnalysisRunRepository(db_session)
    run = AnalysisRun(
        user_id=other_id,
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
    await db_session.commit()

    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "ar1@example.com", "password": "password123"},
    )
    me2 = (await client.get("/api/v1/me")).json()
    assert uuid.UUID(me2["id"]) == owner_id

    forbidden = await client.get(f"/api/v1/analysis-runs/{run.id}")
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_list_analysis_segments_ordered_by_segment_index(client, db_session):
    await _register(client, "arseg@example.com")
    me = (await client.get("/api/v1/me")).json()
    user_id = uuid.UUID(me["id"])

    item_repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=user_id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="x",
        status="COMPLETED",
        original_user_input="q",
        analysis_mode="NOT_APPLICABLE",
        disclaimer="d",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await item_repo.add(item)

    run_repo = AnalysisRunRepository(db_session)
    run = AnalysisRun(
        user_id=user_id,
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
    s2 = AnalysisSegment(
        analysis_run_id=run.id,
        source_segment_id=None,
        segment_index=2,
        title="two",
        start_offset_seconds=None,
        end_offset_seconds=None,
        requested_research_mode="STANDARD",
        actual_research_mode="STANDARD",
        status="COMPLETED",
        downgrade_reason=None,
        can_rerun=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    s0 = AnalysisSegment(
        analysis_run_id=run.id,
        source_segment_id=None,
        segment_index=0,
        title="zero",
        start_offset_seconds=None,
        end_offset_seconds=None,
        requested_research_mode="STANDARD",
        actual_research_mode="STANDARD",
        status="COMPLETED",
        downgrade_reason=None,
        can_rerun=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    s1 = AnalysisSegment(
        analysis_run_id=run.id,
        source_segment_id=None,
        segment_index=1,
        title="one",
        start_offset_seconds=None,
        end_offset_seconds=None,
        requested_research_mode="STANDARD",
        actual_research_mode="STANDARD",
        status="COMPLETED",
        downgrade_reason=None,
        can_rerun=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await seg_repo.add(s2)
    await seg_repo.add(s0)
    await seg_repo.add(s1)
    await db_session.commit()

    resp = await client.get(f"/api/v1/analysis-runs/{run.id}/segments")
    assert resp.status_code == 200
    body = resp.json()
    indexes = [x["segmentIndex"] for x in body["items"]]
    assert indexes == [0, 1, 2]

