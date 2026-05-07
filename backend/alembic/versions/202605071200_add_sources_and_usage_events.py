"""add sources and usage_events

Revision ID: 202605071200
Revises: 202605061428
Create Date: 2026-05-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "202605071200"
down_revision: Union[str, Sequence[str], None] = "202605061428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not insp.has_table("sources"):
        op.create_table(
            "sources",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_type", sa.String(length=50), nullable=False),
            sa.Column("source_access_method", sa.String(length=50), nullable=False),
            sa.Column("source_access_status", sa.String(length=50), nullable=False),
            sa.Column("original_input", sa.Text(), nullable=False),
            sa.Column("normalized_url", sa.Text(), nullable=True),
            sa.Column("file_key", sa.Text(), nullable=True),
            sa.Column("file_name", sa.String(length=512), nullable=True),
            sa.Column("mime_type", sa.String(length=120), nullable=True),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("publisher", sa.Text(), nullable=True),
            sa.Column("author", sa.Text(), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("extracted_text", sa.Text(), nullable=True),
            sa.Column("extracted_text_word_count", sa.Integer(), nullable=True),
            sa.Column("extraction_confidence", sa.String(length=50), nullable=True),
            sa.Column("extraction_error", sa.Text(), nullable=True),
            sa.Column("raw_text_retention", sa.String(length=50), nullable=False),
            sa.Column("content_hash", sa.String(length=255), nullable=True),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("source_complexity", sa.String(length=50), nullable=True),
            sa.Column("segment_count", sa.Integer(), nullable=True),
            sa.Column("scan_status", sa.String(length=50), nullable=True),
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
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_sources_user_id"), "sources", ["user_id"], unique=False)

    if not insp.has_table("usage_events"):
        op.create_table(
            "usage_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("research_item_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("model_provider", sa.String(length=100), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("input_tokens", sa.Integer(), nullable=True),
            sa.Column("output_tokens", sa.Integer(), nullable=True),
            sa.Column("estimated_allowance_impact_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("actual_allowance_impact_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("internal_cost_score", sa.Numeric(12, 4), nullable=True),
            sa.Column("estimated_cost_usd", sa.Numeric(10, 4), nullable=True),
            sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_usage_events_event_type"), "usage_events", ["event_type"], unique=False
        )
        op.create_index(
            op.f("ix_usage_events_source_id"), "usage_events", ["source_id"], unique=False
        )
        op.create_index(
            op.f("ix_usage_events_user_id"), "usage_events", ["user_id"], unique=False
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if insp.has_table("usage_events"):
        op.drop_index(op.f("ix_usage_events_user_id"), table_name="usage_events")
        op.drop_index(op.f("ix_usage_events_source_id"), table_name="usage_events")
        op.drop_index(op.f("ix_usage_events_event_type"), table_name="usage_events")
        op.drop_table("usage_events")

    if insp.has_table("sources"):
        op.drop_index(op.f("ix_sources_user_id"), table_name="sources")
        op.drop_table("sources")
