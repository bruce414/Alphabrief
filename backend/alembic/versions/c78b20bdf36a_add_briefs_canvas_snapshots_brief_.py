"""add briefs canvas_snapshots brief_versions

Revision ID: c78b20bdf36a
Revises: 202605082300
Create Date: 2026-05-08 20:24:03.910110

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c78b20bdf36a'
down_revision: Union[str, Sequence[str], None] = '202605082300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "canvas_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "selected_block_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "selected_source_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("canvas_hash", sa.String(length=255), nullable=True),
        sa.Column(
            "snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
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
    )
    op.create_index("ix_canvas_snapshots_project_id", "canvas_snapshots", ["project_id"])
    op.create_index("ix_canvas_snapshots_user_id", "canvas_snapshots", ["user_id"])

    op.create_table(
        "brief_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brief_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("briefs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "canvas_snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canvas_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=True),
        sa.Column(
            "sections",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("summary_of_changes", sa.Text(), nullable=True),
        sa.Column("generated_from_block_count", sa.Integer(), nullable=True),
        sa.Column("model_provider", sa.String(length=100), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
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
    )

    op.create_index("ix_brief_versions_brief_id", "brief_versions", ["brief_id"])
    op.create_index("ix_brief_versions_project_id", "brief_versions", ["project_id"])
    op.create_index("ix_brief_versions_user_id", "brief_versions", ["user_id"])
    op.create_index("ix_brief_versions_canvas_snapshot_id", "brief_versions", ["canvas_snapshot_id"])

    # Extend existing `briefs` for v0.3 fields without breaking legacy endpoints.
    op.add_column("briefs", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_briefs_project_id", "briefs", ["project_id"])
    op.create_foreign_key(
        "fk_briefs_project_id_projects",
        "briefs",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column("briefs", sa.Column("subject", sa.Text(), nullable=True))
    op.add_column("briefs", sa.Column("ticker", sa.String(length=20), nullable=True))

    op.add_column("briefs", sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_briefs_current_version_id", "briefs", ["current_version_id"])
    op.create_foreign_key(
        "fk_briefs_current_version_id_brief_versions",
        "briefs",
        "brief_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("briefs", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "briefs",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("briefs", "metadata")
    op.drop_column("briefs", "archived_at")

    op.drop_constraint("fk_briefs_current_version_id_brief_versions", "briefs", type_="foreignkey")
    op.drop_index("ix_briefs_current_version_id", table_name="briefs")
    op.drop_column("briefs", "current_version_id")

    op.drop_column("briefs", "ticker")
    op.drop_column("briefs", "subject")

    op.drop_constraint("fk_briefs_project_id_projects", "briefs", type_="foreignkey")
    op.drop_index("ix_briefs_project_id", table_name="briefs")
    op.drop_column("briefs", "project_id")

    op.drop_index("ix_brief_versions_canvas_snapshot_id", table_name="brief_versions")
    op.drop_index("ix_brief_versions_user_id", table_name="brief_versions")
    op.drop_index("ix_brief_versions_project_id", table_name="brief_versions")
    op.drop_index("ix_brief_versions_brief_id", table_name="brief_versions")
    op.drop_table("brief_versions")

    op.drop_index("ix_canvas_snapshots_user_id", table_name="canvas_snapshots")
    op.drop_index("ix_canvas_snapshots_project_id", table_name="canvas_snapshots")
    op.drop_table("canvas_snapshots")
