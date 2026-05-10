"""replace candidate_blocks with candidate_elements

Revision ID: 202605102110
Revises: 202605102100
Create Date: 2026-05-10

Creates candidate_elements per DATA_MODEL 4.12 (block_type renamed to suggested_element_type,
content_json added). Drops obsolete candidate_blocks; no data migration.

Downgrade recreates candidate_blocks to match revision 202605082101.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "202605102110"
down_revision: Union[str, Sequence[str], None] = "202605102100"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_elements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "chat_turn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_turns.id", ondelete="CASCADE"),
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
        sa.Column("suggested_element_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column(
            "content_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "promoted_element_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canvas_elements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("extraction_model_name", sa.String(length=128), nullable=True),
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
    op.create_index(
        "ix_candidate_elements_chat_turn_id",
        "candidate_elements",
        ["chat_turn_id"],
    )
    op.create_index(
        "ix_candidate_elements_project_id",
        "candidate_elements",
        ["project_id"],
    )
    op.create_index(
        "ix_candidate_elements_user_id",
        "candidate_elements",
        ["user_id"],
    )
    op.create_index(
        "ix_candidate_elements_status",
        "candidate_elements",
        ["status"],
    )
    op.create_index(
        "ix_candidate_elements_promoted_element_id",
        "candidate_elements",
        ["promoted_element_id"],
    )

    op.drop_index("ix_candidate_blocks_promoted_block_id", table_name="candidate_blocks")
    op.drop_index("ix_candidate_blocks_status", table_name="candidate_blocks")
    op.drop_index("ix_candidate_blocks_user_id", table_name="candidate_blocks")
    op.drop_index("ix_candidate_blocks_project_id", table_name="candidate_blocks")
    op.drop_index("ix_candidate_blocks_chat_turn_id", table_name="candidate_blocks")
    op.drop_table("candidate_blocks")


def downgrade() -> None:
    op.create_table(
        "candidate_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "chat_turn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_turns.id", ondelete="CASCADE"),
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
        sa.Column("block_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "promoted_block_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canvas_blocks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("extraction_model_name", sa.String(length=128), nullable=True),
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
    op.create_index("ix_candidate_blocks_chat_turn_id", "candidate_blocks", ["chat_turn_id"])
    op.create_index("ix_candidate_blocks_project_id", "candidate_blocks", ["project_id"])
    op.create_index("ix_candidate_blocks_user_id", "candidate_blocks", ["user_id"])
    op.create_index("ix_candidate_blocks_status", "candidate_blocks", ["status"])
    op.create_index(
        "ix_candidate_blocks_promoted_block_id",
        "candidate_blocks",
        ["promoted_block_id"],
    )

    op.drop_index(
        "ix_candidate_elements_promoted_element_id",
        table_name="candidate_elements",
    )
    op.drop_index("ix_candidate_elements_status", table_name="candidate_elements")
    op.drop_index("ix_candidate_elements_user_id", table_name="candidate_elements")
    op.drop_index("ix_candidate_elements_project_id", table_name="candidate_elements")
    op.drop_index("ix_candidate_elements_chat_turn_id", table_name="candidate_elements")
    op.drop_table("candidate_elements")
