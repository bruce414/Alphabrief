"""add research items, jobs, analysis runs/segments

Revision ID: 202605071500
Revises: 202605071400
Create Date: 2026-05-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "202605071500"
down_revision: Union[str, Sequence[str], None] = "202605071400"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not insp.has_table("research_items"):
        op.create_table(
            "research_items",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("item_type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("original_user_input", sa.Text(), nullable=False),
            sa.Column("output_markdown", sa.Text(), nullable=True),
            sa.Column("output_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("short_summary", sa.Text(), nullable=True),
            sa.Column("confidence_label", sa.String(length=50), nullable=True),
            sa.Column("confidence_explanation", sa.Text(), nullable=True),
            sa.Column("analysis_mode", sa.String(length=50), nullable=False),
            sa.Column("disclaimer", sa.Text(), nullable=False),
            sa.Column("model_provider", sa.String(length=100), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("prompt_version", sa.String(length=50), nullable=True),
            sa.Column("error_code", sa.String(length=100), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("requested_research_mode", sa.String(length=50), nullable=True),
            sa.Column("completion_strategy", sa.String(length=50), nullable=True),
            sa.Column("coverage_mode", sa.String(length=50), nullable=True),
            sa.Column(
                "analysis_depth_summary",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
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
            sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_research_items_user_id"), "research_items", ["user_id"], unique=False)
        op.create_index(op.f("ix_research_items_source_id"), "research_items", ["source_id"], unique=False)
        op.create_index(op.f("ix_research_items_item_type"), "research_items", ["item_type"], unique=False)
        op.create_index(op.f("ix_research_items_status"), "research_items", ["status"], unique=False)

    if not insp.has_table("generation_jobs"):
        op.create_table(
            "generation_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("research_item_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("job_type", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("current_step", sa.String(length=80), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_code", sa.String(length=100), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
                ["research_item_id"], ["research_items.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_generation_jobs_user_id"), "generation_jobs", ["user_id"], unique=False)
        op.create_index(op.f("ix_generation_jobs_research_item_id"), "generation_jobs", ["research_item_id"], unique=False)
        op.create_index(op.f("ix_generation_jobs_job_type"), "generation_jobs", ["job_type"], unique=False)
        op.create_index(op.f("ix_generation_jobs_status"), "generation_jobs", ["status"], unique=False)

    if not insp.has_table("analysis_runs"):
        op.create_table(
            "analysis_runs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("research_item_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("source_scan_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("generation_job_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("requested_output_mode", sa.String(length=50), nullable=False),
            sa.Column("analysis_intent", sa.String(length=50), nullable=False),
            sa.Column("requested_research_mode", sa.String(length=50), nullable=False),
            sa.Column("completion_strategy", sa.String(length=50), nullable=False),
            sa.Column("coverage_mode", sa.String(length=50), nullable=False),
            sa.Column("focus_question", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("error_code", sa.String(length=100), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("estimated_allowance_impact_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("actual_allowance_impact_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("warning_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("allowance_before_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("allowance_after_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            sa.ForeignKeyConstraint(["generation_job_id"], ["generation_jobs.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["research_item_id"], ["research_items.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["source_scan_id"], ["source_scans.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_analysis_runs_user_id"), "analysis_runs", ["user_id"], unique=False)
        op.create_index(op.f("ix_analysis_runs_research_item_id"), "analysis_runs", ["research_item_id"], unique=False)
        op.create_index(op.f("ix_analysis_runs_source_id"), "analysis_runs", ["source_id"], unique=False)
        op.create_index(op.f("ix_analysis_runs_source_scan_id"), "analysis_runs", ["source_scan_id"], unique=False)
        op.create_index(op.f("ix_analysis_runs_generation_job_id"), "analysis_runs", ["generation_job_id"], unique=False)
        op.create_index(op.f("ix_analysis_runs_status"), "analysis_runs", ["status"], unique=False)

    if not insp.has_table("analysis_segments"):
        op.create_table(
            "analysis_segments",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("analysis_run_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_segment_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("segment_index", sa.Integer(), nullable=False),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("start_offset_seconds", sa.Integer(), nullable=True),
            sa.Column("end_offset_seconds", sa.Integer(), nullable=True),
            sa.Column("requested_research_mode", sa.String(length=50), nullable=False),
            sa.Column("actual_research_mode", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("downgrade_reason", sa.String(length=80), nullable=True),
            sa.Column("analysis_markdown", sa.Text(), nullable=True),
            sa.Column("analysis_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("key_entities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("key_topics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("can_rerun", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("rerun_of_segment_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["rerun_of_segment_id"], ["analysis_segments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["source_segment_id"], ["source_segments.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_analysis_segments_analysis_run_id"), "analysis_segments", ["analysis_run_id"], unique=False)
        op.create_index(op.f("ix_analysis_segments_source_segment_id"), "analysis_segments", ["source_segment_id"], unique=False)
        op.create_index(op.f("ix_analysis_segments_segment_index"), "analysis_segments", ["segment_index"], unique=False)
        op.create_index(op.f("ix_analysis_segments_status"), "analysis_segments", ["status"], unique=False)
        op.create_index(op.f("ix_analysis_segments_rerun_of_segment_id"), "analysis_segments", ["rerun_of_segment_id"], unique=False)

    if insp.has_table("usage_events"):
        cols = {c["name"] for c in insp.get_columns("usage_events")}
        fks = {fk["name"] for fk in insp.get_foreign_keys("usage_events")}

        if "research_item_id" in cols:
            if op.f("ix_usage_events_research_item_id") not in {i["name"] for i in insp.get_indexes("usage_events")}:
                op.create_index(
                    op.f("ix_usage_events_research_item_id"),
                    "usage_events",
                    ["research_item_id"],
                    unique=False,
                )

            if "fk_usage_events_research_item_id_research_items" not in fks:
                op.create_foreign_key(
                    "fk_usage_events_research_item_id_research_items",
                    "usage_events",
                    "research_items",
                    ["research_item_id"],
                    ["id"],
                    ondelete="SET NULL",
                )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if insp.has_table("usage_events"):
        for fk in insp.get_foreign_keys("usage_events"):
            if fk.get("referred_table") == "research_items" and fk.get("name"):
                op.drop_constraint(fk["name"], "usage_events", type_="foreignkey")
        indexes = {i["name"] for i in insp.get_indexes("usage_events")}
        if op.f("ix_usage_events_research_item_id") in indexes:
            op.drop_index(op.f("ix_usage_events_research_item_id"), table_name="usage_events")

    if insp.has_table("analysis_segments"):
        op.drop_index(op.f("ix_analysis_segments_rerun_of_segment_id"), table_name="analysis_segments")
        op.drop_index(op.f("ix_analysis_segments_status"), table_name="analysis_segments")
        op.drop_index(op.f("ix_analysis_segments_segment_index"), table_name="analysis_segments")
        op.drop_index(op.f("ix_analysis_segments_source_segment_id"), table_name="analysis_segments")
        op.drop_index(op.f("ix_analysis_segments_analysis_run_id"), table_name="analysis_segments")
        op.drop_table("analysis_segments")

    if insp.has_table("analysis_runs"):
        op.drop_index(op.f("ix_analysis_runs_status"), table_name="analysis_runs")
        op.drop_index(op.f("ix_analysis_runs_generation_job_id"), table_name="analysis_runs")
        op.drop_index(op.f("ix_analysis_runs_source_scan_id"), table_name="analysis_runs")
        op.drop_index(op.f("ix_analysis_runs_source_id"), table_name="analysis_runs")
        op.drop_index(op.f("ix_analysis_runs_research_item_id"), table_name="analysis_runs")
        op.drop_index(op.f("ix_analysis_runs_user_id"), table_name="analysis_runs")
        op.drop_table("analysis_runs")

    if insp.has_table("generation_jobs"):
        op.drop_index(op.f("ix_generation_jobs_status"), table_name="generation_jobs")
        op.drop_index(op.f("ix_generation_jobs_job_type"), table_name="generation_jobs")
        op.drop_index(op.f("ix_generation_jobs_research_item_id"), table_name="generation_jobs")
        op.drop_index(op.f("ix_generation_jobs_user_id"), table_name="generation_jobs")
        op.drop_table("generation_jobs")

    if insp.has_table("research_items"):
        op.drop_index(op.f("ix_research_items_status"), table_name="research_items")
        op.drop_index(op.f("ix_research_items_item_type"), table_name="research_items")
        op.drop_index(op.f("ix_research_items_source_id"), table_name="research_items")
        op.drop_index(op.f("ix_research_items_user_id"), table_name="research_items")
        op.drop_table("research_items")

