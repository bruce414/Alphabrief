"""add users full schema

Revision ID: 202605061428
Revises: caae2dd1f978
Create Date: 2026-05-06

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "202605061428"
down_revision: Union[str, Sequence[str], None] = "caae2dd1f978"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _user_column_names(conn) -> set[str]:
    insp = inspect(conn)
    return {c["name"] for c in insp.get_columns("users")}


def _varchar_length(conn, table: str, column: str) -> int | None:
    """Return declared VARCHAR length if present (else None for unbounded / non-varchar)."""
    insp = inspect(conn)
    for c in insp.get_columns(table):
        if c["name"] == column:
            return getattr(c["type"], "length", None)
    return None


def upgrade() -> None:
    """
    Idempotent: local DBs may already match the target schema (e.g. created via
    ``Base.metadata.create_all``) while ``alembic_version`` lags, so blind ``add_column`` fails.
    """
    bind = op.get_bind()

    # Widen / narrow only when the source column still has the old migration length.
    if _varchar_length(bind, "users", "email") == 320:
        op.alter_column(
            "users",
            "email",
            existing_type=sa.String(length=320),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
    if _varchar_length(bind, "users", "display_name") == 255:
        op.alter_column(
            "users",
            "display_name",
            existing_type=sa.String(length=255),
            type_=sa.String(length=120),
            existing_nullable=True,
        )

    cols = _user_column_names(bind)

    if "password_hash" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "password_hash",
                sa.String(length=255),
                nullable=False,
                server_default="",
            ),
        )
    if "role" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "role",
                sa.String(length=50),
                nullable=False,
                server_default="USER",
            ),
        )
    if "default_output_mode" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "default_output_mode",
                sa.String(length=50),
                nullable=False,
                server_default="ASK",
            ),
        )
    if "default_research_scope" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "default_research_scope",
                sa.String(length=50),
                nullable=False,
                server_default="RECOMMENDED_CONTEXT",
            ),
        )
    if "default_research_mode" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "default_research_mode",
                sa.String(length=50),
                nullable=False,
                server_default="STANDARD",
            ),
        )
    if "optimize_research_default" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "optimize_research_default",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )

    # Clear server defaults from columns this migration is responsible for (if still set).
    for col in (
        "password_hash",
        "role",
        "default_output_mode",
        "default_research_scope",
        "default_research_mode",
        "optimize_research_default",
    ):
        if col in _user_column_names(bind):
            op.alter_column("users", col, server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    cols = _user_column_names(bind)

    for name in (
        "optimize_research_default",
        "default_research_mode",
        "default_research_scope",
        "default_output_mode",
        "role",
        "password_hash",
    ):
        if name in cols:
            op.drop_column("users", name)

    if _varchar_length(bind, "users", "display_name") == 120:
        op.alter_column(
            "users",
            "display_name",
            existing_type=sa.String(length=120),
            type_=sa.String(length=255),
            existing_nullable=True,
        )
    if _varchar_length(bind, "users", "email") == 255:
        op.alter_column(
            "users",
            "email",
            existing_type=sa.String(length=255),
            type_=sa.String(length=320),
            existing_nullable=False,
        )

