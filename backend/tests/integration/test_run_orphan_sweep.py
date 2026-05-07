"""Integration: startup orphan sweep marks stale RUNNING rows FAILED."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app.main import _sweep_orphaned_runs
from app.models.analysis_run import AnalysisRun
from app.models.generation_job import GenerationJob
from app.models.research_item import ResearchItem


class _SameSessionContext:
    def __init__(self, session) -> None:
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *args: object) -> bool:
        return False


async def _register(client, email: str, password: str = "password123") -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_orphan_sweep_marks_stale_running_failed(client, db_session, monkeypatch):
    await _register(client, "orphan@example.com")
    me = (await client.get("/api/v1/me")).json()
    user_id = uuid.UUID(me["id"])

    item = ResearchItem(
        user_id=user_id,
        source_id=None,
        item_type="SOURCE_ANALYSIS",
        title="x",
        status="RUNNING",
        original_user_input="q",
        analysis_mode="SOURCE_BRIEF",
        disclaimer="d",
    )
    db_session.add(item)
    await db_session.flush()

    job = GenerationJob(
        user_id=user_id,
        research_item_id=item.id,
        job_type="ADAPTIVE_SOURCE_ANALYSIS",
        status="RUNNING",
    )
    db_session.add(job)
    await db_session.flush()

    run = AnalysisRun(
        user_id=user_id,
        research_item_id=item.id,
        source_id=None,
        source_scan_id=None,
        generation_job_id=job.id,
        requested_output_mode="ASK",
        analysis_intent="MARKET_IMPACT",
        requested_research_mode="STANDARD",
        completion_strategy="STRICT_REQUESTED_MODE",
        coverage_mode="FULL_SOURCE",
        status="RUNNING",
        warning_acknowledged=True,
    )
    db_session.add(run)
    await db_session.commit()

    old = datetime.now(UTC) - timedelta(minutes=30)
    await db_session.execute(
        update(AnalysisRun)
        .where(AnalysisRun.id == run.id)
        .values(updated_at=old)
    )
    await db_session.execute(
        update(GenerationJob)
        .where(GenerationJob.id == job.id)
        .values(updated_at=old)
    )
    await db_session.execute(
        update(ResearchItem)
        .where(ResearchItem.id == item.id)
        .values(updated_at=old)
    )
    await db_session.commit()

    monkeypatch.setattr(
        "app.db.session.async_session_factory",
        lambda: _SameSessionContext(db_session),
    )
    await _sweep_orphaned_runs()

    r = (
        await db_session.execute(select(AnalysisRun).where(AnalysisRun.id == run.id))
    ).scalar_one()
    assert r is not None
    assert r.status == "FAILED"
    assert r.error_code == "RUN_ORPHANED"
