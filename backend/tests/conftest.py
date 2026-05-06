"""Pytest fixtures: async HTTP client and a fresh ORM schema once per session."""

from __future__ import annotations

import os

# Resolve Settings before the app imports the async engine.
os.environ.setdefault("ENVIRONMENT", "test")

import app.models  # noqa: F401 - register models on Base.metadata
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_schema() -> None:
    """Drop and recreate tables from ORM metadata (requires a disposable Postgres DB)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
