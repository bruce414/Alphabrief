"""add source_fetch_policies and source_fetch_log

Revision ID: 202605071230
Revises: 202605071200
Create Date: 2026-05-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "202605071230"
down_revision: Union[str, Sequence[str], None] = "202605071200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not insp.has_table("source_fetch_policies"):
        op.create_table(
            "source_fetch_policies",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("domain", sa.String(length=255), nullable=False),
            sa.Column("robots_txt_url", sa.Text(), nullable=True),
            sa.Column("robots_txt_content", sa.Text(), nullable=True),
            sa.Column("robots_fetched_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("robots_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("robots_status", sa.Integer(), nullable=True),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("domain"),
        )
        op.create_index(
            op.f("ix_source_fetch_policies_domain"),
            "source_fetch_policies",
            ["domain"],
            unique=False,
        )

    if not insp.has_table("source_fetch_log"):
        op.create_table(
            "source_fetch_log",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("domain", sa.String(length=255), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("robots_decision", sa.String(length=50), nullable=True),
            sa.Column("response_status", sa.Integer(), nullable=True),
            sa.Column("content_length", sa.Integer(), nullable=True),
            sa.Column("action_taken", sa.String(length=50), nullable=False),
            sa.Column("denied_reason", sa.String(length=120), nullable=True),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_source_fetch_log_domain"), "source_fetch_log", ["domain"], unique=False)
        op.create_index(op.f("ix_source_fetch_log_source_id"), "source_fetch_log", ["source_id"], unique=False)
        op.create_index(op.f("ix_source_fetch_log_user_id"), "source_fetch_log", ["user_id"], unique=False)
        op.create_index(op.f("ix_source_fetch_log_created_at"), "source_fetch_log", ["created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if insp.has_table("source_fetch_log"):
        op.drop_index(op.f("ix_source_fetch_log_created_at"), table_name="source_fetch_log")
        op.drop_index(op.f("ix_source_fetch_log_user_id"), table_name="source_fetch_log")
        op.drop_index(op.f("ix_source_fetch_log_source_id"), table_name="source_fetch_log")
        op.drop_index(op.f("ix_source_fetch_log_domain"), table_name="source_fetch_log")
        op.drop_table("source_fetch_log")

    if insp.has_table("source_fetch_policies"):
        op.drop_index(op.f("ix_source_fetch_policies_domain"), table_name="source_fetch_policies")
        op.drop_table("source_fetch_policies")

