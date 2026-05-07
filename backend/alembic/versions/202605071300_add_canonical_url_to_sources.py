"""add canonical_url to sources

Revision ID: 202605071300
Revises: 202605071230
Create Date: 2026-05-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "202605071300"
down_revision: Union[str, Sequence[str], None] = "202605071230"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("sources"):
        return
    cols = {c["name"] for c in insp.get_columns("sources")}
    if "canonical_url" not in cols:
        op.add_column("sources", sa.Column("canonical_url", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("sources"):
        return
    cols = {c["name"] for c in insp.get_columns("sources")}
    if "canonical_url" in cols:
        op.drop_column("sources", "canonical_url")
