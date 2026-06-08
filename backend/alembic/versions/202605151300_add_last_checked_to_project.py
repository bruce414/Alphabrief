"""add_last_checked_to_project

Revision ID: 202605151300
Revises: 202605151200
Create Date: 2026-05-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202605151300"
down_revision: Union[str, Sequence[str], None] = "202605151200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "projects",
        sa.Column("updates_available_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("projects", "updates_available_count")
    op.drop_column("projects", "last_checked_at")
