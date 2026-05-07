"""add source_scans and source_segments

Revision ID: 202605071330
Revises: 202605071300
Create Date: 2026-05-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "202605071330"
down_revision: Union[str, Sequence[str], None] = "202605071300"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not insp.has_table("source_scans"):
        op.create_table(
            "source_scans",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("requested_output_mode", sa.String(length=50), nullable=False),
            sa.Column("analysis_intent", sa.String(length=50), nullable=False),
            sa.Column("requested_research_mode", sa.String(length=50), nullable=False),
            sa.Column("coverage_mode", sa.String(length=50), nullable=False),
            sa.Column("focus_question", sa.Text(), nullable=True),
            sa.Column("source_complexity", sa.String(length=50), nullable=False),
            sa.Column("estimate_confidence", sa.String(length=50), nullable=False),
            sa.Column(
                "estimated_allowance_impact_percent",
                sa.Numeric(5, 2),
                nullable=False,
            ),
            sa.Column("requires_warning", sa.Boolean(), nullable=False),
            sa.Column("warning_level", sa.String(length=50), nullable=False),
            sa.Column("recommended_research_mode", sa.String(length=50), nullable=False),
            sa.Column(
                "recommended_completion_strategy", sa.String(length=50), nullable=False
            ),
            sa.Column(
                "detected_topics",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column(
                "detected_entities",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
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
            sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_source_scans_source_id"), "source_scans", ["source_id"], unique=False
        )
        op.create_index(
            op.f("ix_source_scans_user_id"), "source_scans", ["user_id"], unique=False
        )

    if not insp.has_table("source_segments"):
        op.create_table(
            "source_segments",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_scan_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("segment_index", sa.Integer(), nullable=False),
            sa.Column("start_offset_seconds", sa.Integer(), nullable=True),
            sa.Column("end_offset_seconds", sa.Integer(), nullable=True),
            sa.Column("start_char_offset", sa.Integer(), nullable=True),
            sa.Column("end_char_offset", sa.Integer(), nullable=True),
            sa.Column("page_start", sa.Integer(), nullable=True),
            sa.Column("page_end", sa.Integer(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("topic_summary", sa.Text(), nullable=True),
            sa.Column(
                "detected_entities",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column(
                "detected_topics",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column("estimated_complexity", sa.String(length=50), nullable=True),
            sa.Column("relevance_to_intent", sa.String(length=50), nullable=True),
            sa.Column("recommended_research_mode", sa.String(length=50), nullable=True),
            sa.Column(
                "metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False
            ),
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
            sa.ForeignKeyConstraint(
                ["source_id"], ["sources.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["source_scan_id"], ["source_scans.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_source_segments_source_id"),
            "source_segments",
            ["source_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_source_segments_source_scan_id"),
            "source_segments",
            ["source_scan_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if insp.has_table("source_segments"):
        op.drop_index(
            op.f("ix_source_segments_source_scan_id"), table_name="source_segments"
        )
        op.drop_index(
            op.f("ix_source_segments_source_id"), table_name="source_segments"
        )
        op.drop_table("source_segments")

    if insp.has_table("source_scans"):
        op.drop_index(op.f("ix_source_scans_user_id"), table_name="source_scans")
        op.drop_index(op.f("ix_source_scans_source_id"), table_name="source_scans")
        op.drop_table("source_scans")
