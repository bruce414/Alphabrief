"""add overview fields to project

Revision ID: 202605151200
Revises: 202605102200
Create Date: 2026-05-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "202605151200"
down_revision: Union[str, Sequence[str], None] = "202605102200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("research_goal", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("research_type", sa.String(length=64), nullable=True))
    op.add_column(
        "projects",
        sa.Column(
            "included_topics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "excluded_topics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "target_entities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column("projects", sa.Column("time_horizon", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "time_horizon")
    op.drop_column("projects", "target_entities")
    op.drop_column("projects", "excluded_topics")
    op.drop_column("projects", "included_topics")
    op.drop_column("projects", "research_type")
    op.drop_column("projects", "research_goal")
