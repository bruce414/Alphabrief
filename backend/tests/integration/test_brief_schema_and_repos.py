from __future__ import annotations

import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.session import get_engine
from app.models.brief import Brief
from app.models.brief_version import BriefVersion
from app.models.canvas_snapshot import CanvasSnapshot
from app.models.project import Project
from app.models.user import User
from app.repositories.brief_repository import BriefRepository
from app.repositories.brief_version_repository import BriefVersionRepository
from app.repositories.canvas_snapshot_repository import CanvasSnapshotRepository


def _repo_root() -> Path:
    # backend/tests/... -> repo root
    return Path(__file__).resolve().parents[3]


@pytest.mark.asyncio
async def test_migration_upgrade_downgrade_cleanly_and_single_head():
    repo = _repo_root()
    backend_dir = repo / "backend"
    alembic_ini = backend_dir / "alembic.ini"

    env = dict(os.environ)
    env.setdefault("ENVIRONMENT", "test")

    # Reset DB schema to a known empty state, then run migrations.
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    def _run(*args: str) -> None:
        p = subprocess.run(
            args,
            cwd=str(backend_dir),
            env=env,
            capture_output=True,
            text=True,
        )
        assert p.returncode == 0, f"Command failed: {' '.join(args)}\n{p.stdout}\n{p.stderr}"

    # Heads = 1
    p_heads = subprocess.run(
        ["alembic", "-c", str(alembic_ini), "heads"],
        cwd=str(backend_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    assert p_heads.returncode == 0
    # Alembic prints one line per head. Keep this strict.
    head_lines = [ln for ln in p_heads.stdout.splitlines() if ln.strip()]
    assert len(head_lines) == 1

    _run("alembic", "-c", str(alembic_ini), "upgrade", "head")
    _run("alembic", "-c", str(alembic_ini), "downgrade", "base")
    _run("alembic", "-c", str(alembic_ini), "upgrade", "head")


@pytest.mark.asyncio
async def test_canvas_snapshots_uuid_array_round_trips(db_session):
    user = User(email="snap@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    project = Project(user_id=user.id, kind="THESIS", title="P", description=None)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    block_ids = [uuid.uuid4(), uuid.uuid4()]
    source_ids = [uuid.uuid4()]

    repo = CanvasSnapshotRepository(db_session)
    created = await repo.create(
        CanvasSnapshot(
            project_id=project.id,
            user_id=user.id,
            selected_block_ids=block_ids,
            selected_source_ids=source_ids,
            canvas_hash=None,
            snapshot_json={"blocks": []},
        )
    )
    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.selected_block_ids == block_ids
    assert fetched.selected_source_ids == source_ids


@pytest.mark.asyncio
async def test_brief_versions_archived_at_exists_and_nullable(db_session):
    def _check(sync_conn) -> None:
        insp = inspect(sync_conn)
        cols = {c["name"]: c for c in insp.get_columns("brief_versions")}
        assert "archived_at" in cols
        assert cols["archived_at"]["nullable"] is True

    conn = await db_session.connection()
    await conn.run_sync(_check)


@pytest.mark.asyncio
async def test_repositories_round_trip_for_brief_and_brief_version(db_session):
    user = User(email="repo@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    project = Project(user_id=user.id, kind="THESIS", title="P", description=None)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    snap_repo = CanvasSnapshotRepository(db_session)
    snapshot = await snap_repo.create(
        CanvasSnapshot(
            project_id=project.id,
            user_id=user.id,
            selected_block_ids=[],
            selected_source_ids=[],
            canvas_hash=None,
            snapshot_json={"blocks": []},
        )
    )

    brief_repo = BriefRepository(db_session)
    brief = await brief_repo.create(
        Brief(
            project_id=project.id,
            user_id=user.id,
            title="T",
            brief_type="THESIS_MEMO",
            status="ACTIVE",
            subject="S",
            ticker="ABC",
            current_version_id=None,
            summary=None,
            archived_at=None,
            metadata_={},
        )
    )

    version_repo = BriefVersionRepository(db_session)
    version = await version_repo.create(
        BriefVersion(
            brief_id=brief.id,
            project_id=project.id,
            user_id=user.id,
            version_number=1,
            canvas_snapshot_id=snapshot.id,
            status="COMPLETED",
            content_markdown="hello",
            sections={"a": 1},
            summary_of_changes=None,
            generated_from_block_count=0,
            model_provider=None,
            model_name=None,
            prompt_version=None,
            disclaimer="Educational use only.",
            archived_at=None,
        )
    )

    # Update brief current_version_id
    brief.current_version_id = version.id
    await brief_repo.update(brief)
    fetched_brief = await brief_repo.get_by_id(brief.id)
    assert fetched_brief is not None
    assert fetched_brief.current_version_id == version.id

    fetched_version = await version_repo.get_by_id(version.id)
    assert fetched_version is not None
    assert fetched_version.canvas_snapshot_id == snapshot.id


@pytest.mark.asyncio
async def test_briefs_current_version_id_fk_enforces_integrity(db_session):
    user = User(email="fk@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    project = Project(user_id=user.id, kind="THESIS", title="P", description=None)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    bad = Brief(
        project_id=project.id,
        user_id=user.id,
        title="Bad",
        brief_type="THESIS_MEMO",
        status="ACTIVE",
        subject=None,
        ticker=None,
        current_version_id=uuid.uuid4(),
        summary=None,
        archived_at=None,
        metadata_={},
    )
    db_session.add(bad)

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

