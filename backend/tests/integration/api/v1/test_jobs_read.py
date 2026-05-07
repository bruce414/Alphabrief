import uuid
from datetime import datetime, timezone

import pytest

from app.models.generation_job import GenerationJob
from app.models.research_item import ResearchItem
from app.repositories.generation_job_repository import GenerationJobRepository
from app.repositories.research_item_repository import ResearchItemRepository


async def _register(client, email: str) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_get_job_owner_check_via_research_item_and_404(client, db_session):
    await _register(client, "job1@example.com")
    missing = uuid.uuid4()
    r404 = await client.get(f"/api/v1/jobs/{missing}")
    assert r404.status_code == 404

    me = (await client.get("/api/v1/me")).json()
    owner_id = uuid.UUID(me["id"])

    await client.post("/api/v1/auth/logout")
    await _register(client, "job2@example.com")
    other = (await client.get("/api/v1/me")).json()
    other_id = uuid.UUID(other["id"])

    item_repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=other_id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="x",
        status="QUEUED",
        original_user_input="q",
        analysis_mode="NOT_APPLICABLE",
        disclaimer="d",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await item_repo.add(item)

    job_repo = GenerationJobRepository(db_session)
    job = GenerationJob(
        user_id=other_id,
        research_item_id=item.id,
        job_type="ASK_ANALYSIS",
        status="QUEUED",
        current_step=None,
        retry_count=0,
        error_code=None,
        error_message=None,
        started_at=None,
        completed_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await job_repo.add(job)
    await db_session.commit()

    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "job1@example.com", "password": "password123"},
    )
    me2 = (await client.get("/api/v1/me")).json()
    assert uuid.UUID(me2["id"]) == owner_id

    forbidden = await client.get(f"/api/v1/jobs/{job.id}")
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_get_job_happy_path(client, db_session):
    await _register(client, "jobhappy@example.com")
    me = (await client.get("/api/v1/me")).json()
    user_id = uuid.UUID(me["id"])

    item_repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=user_id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="x",
        status="QUEUED",
        original_user_input="q",
        analysis_mode="NOT_APPLICABLE",
        disclaimer="d",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await item_repo.add(item)

    job_repo = GenerationJobRepository(db_session)
    job = GenerationJob(
        user_id=user_id,
        research_item_id=item.id,
        job_type="ASK_ANALYSIS",
        status="RUNNING",
        current_step="GENERATING_OUTPUT",
        retry_count=0,
        error_code=None,
        error_message=None,
        started_at=None,
        completed_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await job_repo.add(job)
    await db_session.commit()

    resp = await client.get(f"/api/v1/jobs/{job.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["jobId"] == str(job.id)
    assert body["researchItemId"] == str(item.id)
    assert body["jobType"] == "ASK_ANALYSIS"
    assert body["status"] == "RUNNING"

