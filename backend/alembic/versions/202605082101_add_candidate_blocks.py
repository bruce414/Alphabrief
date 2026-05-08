"""add candidate_blocks

Revision ID: 202605082101
Revises: c78b20bdf36a
Create Date: 2026-05-08 21:01:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "202605082101"
down_revision: Union[str, Sequence[str], None] = "c78b20bdf36a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
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
    op.create_index("ix_candidate_blocks_promoted_block_id", "candidate_blocks", ["promoted_block_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_candidate_blocks_promoted_block_id", table_name="candidate_blocks")
    op.drop_index("ix_candidate_blocks_status", table_name="candidate_blocks")
    op.drop_index("ix_candidate_blocks_user_id", table_name="candidate_blocks")
    op.drop_index("ix_candidate_blocks_project_id", table_name="candidate_blocks")
    op.drop_index("ix_candidate_blocks_chat_turn_id", table_name="candidate_blocks")
    op.drop_table("candidate_blocks")

