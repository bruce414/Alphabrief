"""Pytest fixtures: async HTTP client + transactional DB session per test."""

from __future__ import annotations

import os

# Resolve Settings before the app imports the async engine.
os.environ.setdefault("ENVIRONMENT", "test")
# Keep tests deterministic and avoid importing Anthropic unless explicitly configured in CI.
os.environ["AI_PROVIDER"] = "mock"

import app.models  # noqa: F401 - register models on Base.metadata
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import pytest

from app.db.base import Base
from app.db.session import get_db, get_engine
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_schema() -> None:
    """Drop and recreate tables once for the test session."""
    engine = get_engine()
    async with engine.begin() as conn:
        # Use schema-level reset to avoid FK name/cycle issues when models evolve.
        await conn.execute(sa.text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(sa.text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = get_engine()
    async with engine.connect() as connection:
        trans = await connection.begin()
        session_maker = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with session_maker() as session:
            await connection.begin_nested()

            @event.listens_for(session.sync_session, "after_transaction_end")
            def _restart_savepoint(sess, transaction):  # type: ignore[no-untyped-def]
                if transaction.nested and not transaction._parent.nested:
                    connection.sync_connection.begin_nested()

            yield session

        await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
