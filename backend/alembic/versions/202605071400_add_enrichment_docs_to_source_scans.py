"""add enrichment_docs to source_scans

Revision ID: 202605071400
Revises: 202605071330
Create Date: 2026-05-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "202605071400"
down_revision: Union[str, Sequence[str], None] = "202605071330"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("source_scans"):
        return
    cols = {c["name"] for c in insp.get_columns("source_scans")}
    if "enrichment_docs" not in cols:
        op.add_column(
            "source_scans",
            sa.Column(
                "enrichment_docs",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'[]'::jsonb"),
                nullable=False,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("source_scans"):
        return
    cols = {c["name"] for c in insp.get_columns("source_scans")}
    if "enrichment_docs" in cols:
        op.drop_column("source_scans", "enrichment_docs")
