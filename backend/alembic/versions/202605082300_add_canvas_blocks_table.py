"""add canvas_blocks table

Revision ID: 202605082300
Revises: 202605082200
Create Date: 2026-05-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "202605082300"
down_revision: Union[str, Sequence[str], None] = "202605082200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "canvas_blocks",
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
        sa.Column("block_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column(
            "content_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("position_index", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("provenance_kind", sa.String(length=32), nullable=False),
        sa.Column(
            "provenance_chat_turn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_turns.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "provenance_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence_label", sa.String(length=50), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
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

    op.create_index("ix_canvas_blocks_project_id", "canvas_blocks", ["project_id"])
    op.create_index("ix_canvas_blocks_user_id", "canvas_blocks", ["user_id"])
    op.create_index("ix_canvas_blocks_position_index", "canvas_blocks", ["position_index"])
    op.create_index("ix_canvas_blocks_provenance_chat_turn_id", "canvas_blocks", ["provenance_chat_turn_id"])
    op.create_index("ix_canvas_blocks_provenance_source_id", "canvas_blocks", ["provenance_source_id"])


def downgrade() -> None:
    op.drop_index("ix_canvas_blocks_provenance_source_id", table_name="canvas_blocks")
    op.drop_index("ix_canvas_blocks_provenance_chat_turn_id", table_name="canvas_blocks")
    op.drop_index("ix_canvas_blocks_position_index", table_name="canvas_blocks")
    op.drop_index("ix_canvas_blocks_user_id", table_name="canvas_blocks")
    op.drop_index("ix_canvas_blocks_project_id", table_name="canvas_blocks")
    op.drop_table("canvas_blocks")

