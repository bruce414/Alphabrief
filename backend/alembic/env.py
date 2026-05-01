"""Alembic migration environment."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

# Ensure `app` resolves no matter which directory launches Alembic (e.g. repo root vs backend/).
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_root_str = str(_BACKEND_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

from sqlalchemy import create_engine, pool

from alembic import context

from app.core.config import settings
from app.core.database import Base

import app.models  # noqa: F401 - load model imports when added under app.models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
