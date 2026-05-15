"""Integration tests for project update check (last_checked_at plumbing)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.enums import ProjectKind
from app.models.project import Project
from app.models.user import User
from app.services.update_check_service import run_update_check


async def _register(client, email: str) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert r.status_code == 201, r.text


async def _create_project(client, *, email_suffix: str) -> str:
    await _register(client, f"update-check-{email_suffix}@example.com")
    created = await client.post(
        "/api/v1/projects",
        json={"title": "Update check project", "kind": "COVERAGE"},
    )
    assert created.status_code == 201
    return created.json()["id"]


@pytest.mark.asyncio
async def test_post_check_updates_sets_last_checked_at(client):
    project_id = await _create_project(client, email_suffix="post-sets")

    resp = await client.post(f"/api/v1/projects/{project_id}/overview/check-updates")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"]["lastCheckedAt"] is not None
    assert body["status"]["updatesAvailableCount"] == 0


@pytest.mark.asyncio
async def test_post_check_updates_advances_timestamp_on_repeat(client, monkeypatch):
    project_id = await _create_project(client, email_suffix="post-idempotent")
    base = datetime(2026, 5, 15, 12, 0, 0, tzinfo=UTC)
    times = [base, base + timedelta(minutes=1)]
    idx = {"i": 0}

    def fake_now() -> datetime:
        t = times[idx["i"]]
        idx["i"] += 1
        return t

    monkeypatch.setattr("app.services.update_check_service._now_utc", fake_now)

    first = await client.post(f"/api/v1/projects/{project_id}/overview/check-updates")
    assert first.status_code == 200
    first_ts = first.json()["status"]["lastCheckedAt"]

    second = await client.post(f"/api/v1/projects/{project_id}/overview/check-updates")
    assert second.status_code == 200
    second_ts = second.json()["status"]["lastCheckedAt"]

    assert first_ts != second_ts
    assert second_ts > first_ts


@pytest.mark.asyncio
async def test_run_update_check_service_direct(db_session):
    user = User(email="svc-update-check@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    project = Project(
        user_id=user.id,
        kind=ProjectKind.COVERAGE.value,
        title="Direct service",
        description=None,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    assert project.last_checked_at is None

    updated = await run_update_check(db_session, project.id)
    assert updated.last_checked_at is not None
    assert updated.updates_available_count == 0


@pytest.mark.asyncio
async def test_get_overview_reflects_last_checked_after_post(client):
    project_id = await _create_project(client, email_suffix="get-after-post")

    before = await client.get(f"/api/v1/projects/{project_id}/overview")
    assert before.status_code == 200
    assert before.json()["status"]["lastCheckedAt"] is None

    checked = await client.post(f"/api/v1/projects/{project_id}/overview/check-updates")
    assert checked.status_code == 200
    checked_at = checked.json()["status"]["lastCheckedAt"]
    assert checked_at is not None

    after = await client.get(f"/api/v1/projects/{project_id}/overview")
    assert after.status_code == 200
    assert after.json()["status"]["lastCheckedAt"] == checked_at


@pytest.mark.asyncio
async def test_post_check_updates_unknown_project_returns_404(client):
    await _register(client, "update-check-404@example.com")

    resp = await client.post(f"/api/v1/projects/{uuid4()}/overview/check-updates")
    assert resp.status_code == 404
    assert resp.json()["errorCode"] == "NOT_FOUND"
