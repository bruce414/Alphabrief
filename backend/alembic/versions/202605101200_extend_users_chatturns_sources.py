"""extend users, chat_turns, sources columns

Revision ID: 202605101200
Revises: 202605082101
Create Date: 2026-05-10

Adds user research defaults (see DATA_MODEL §4.1), chat turn intent / input
detection and token fields (§4.4), and optional source project attachment (§4.6).

Upgrade is idempotent: ``users`` research columns may already exist from
``202605061428``; ``chat_turns`` cache token columns may already exist from
``202605082200``. Downgrade only removes columns/constraints introduced here for
``chat_turns`` and ``sources``; it does not drop ``users`` research columns or
cache token columns when those were created by earlier revisions.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "202605101200"
down_revision: Union[str, Sequence[str], None] = "202605082101"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(conn, table: str) -> set[str]:
    insp = inspect(conn)
    return {c["name"] for c in insp.get_columns(table)}


def _index_names(conn, table: str) -> set[str]:
    insp = inspect(conn)
    return {ix["name"] for ix in insp.get_indexes(table)}


def _fk_names(conn, table: str) -> set[str]:
    insp = inspect(conn)
    return {fk["name"] for fk in insp.get_foreign_keys(table) if fk.get("name")}


def upgrade() -> None:
    bind = op.get_bind()

    # --- users (may already match 202605061428) ---
    ucols = _column_names(bind, "users")
    if "default_research_scope" not in ucols:
        op.add_column(
            "users",
            sa.Column(
                "default_research_scope",
                sa.String(length=50),
                nullable=False,
                server_default="RECOMMENDED_CONTEXT",
            ),
        )
        op.alter_column("users", "default_research_scope", server_default=None)
    if "default_research_mode" not in ucols:
        op.add_column(
            "users",
            sa.Column(
                "default_research_mode",
                sa.String(length=50),
                nullable=False,
                server_default="STANDARD",
            ),
        )
        op.alter_column("users", "default_research_mode", server_default=None)
    if "optimize_research_default" not in ucols:
        op.add_column(
            "users",
            sa.Column(
                "optimize_research_default",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )
        op.alter_column("users", "optimize_research_default", server_default=None)

    # --- chat_turns ---
    tcols = _column_names(bind, "chat_turns")
    if "intent_type" not in tcols:
        op.add_column(
            "chat_turns",
            sa.Column("intent_type", sa.String(length=50), nullable=True),
        )
    if "detected_input_type" not in tcols:
        op.add_column(
            "chat_turns",
            sa.Column("detected_input_type", sa.String(length=50), nullable=True),
        )
    if "cache_read_tokens" not in tcols:
        op.add_column(
            "chat_turns",
            sa.Column("cache_read_tokens", sa.Integer(), nullable=True),
        )
    if "cache_write_tokens" not in tcols:
        op.add_column(
            "chat_turns",
            sa.Column("cache_write_tokens", sa.Integer(), nullable=True),
        )

    # --- sources.project_id → projects ---
    scols = _column_names(bind, "sources")
    if "project_id" not in scols:
        op.add_column(
            "sources",
            sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

    if "fk_sources_project_id" not in _fk_names(bind, "sources"):
        op.create_foreign_key(
            "fk_sources_project_id",
            "sources",
            "projects",
            ["project_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if "idx_sources_project_id" not in _index_names(bind, "sources"):
        op.create_index("idx_sources_project_id", "sources", ["project_id"])


def downgrade() -> None:
    bind = op.get_bind()

    if "idx_sources_project_id" in _index_names(bind, "sources"):
        op.drop_index("idx_sources_project_id", table_name="sources")
    if "fk_sources_project_id" in _fk_names(bind, "sources"):
        op.drop_constraint("fk_sources_project_id", "sources", type_="foreignkey")
    if "project_id" in _column_names(bind, "sources"):
        op.drop_column("sources", "project_id")

    tcols = _column_names(bind, "chat_turns")
    if "intent_type" in tcols:
        op.drop_column("chat_turns", "intent_type")
    if "detected_input_type" in tcols:
        op.drop_column("chat_turns", "detected_input_type")

    # cache_read_tokens / cache_write_tokens are not dropped here: when present from
    # revision 202605082200's chat_turns table, removing them would violate that
    # revision's schema while it remains applied below this one.
