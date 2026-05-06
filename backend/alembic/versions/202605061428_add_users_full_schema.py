"""add users full schema

Revision ID: 202605061428
Revises: caae2dd1f978
Create Date: 2026-05-06

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "202605061428"
down_revision: Union[str, Sequence[str], None] = "caae2dd1f978"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=320),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "display_name",
        existing_type=sa.String(length=255),
        type_=sa.String(length=120),
        existing_nullable=True,
    )

    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            server_default="USER",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "default_output_mode",
            sa.String(length=50),
            nullable=False,
            server_default="ASK",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "default_research_scope",
            sa.String(length=50),
            nullable=False,
            server_default="RECOMMENDED_CONTEXT",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "default_research_mode",
            sa.String(length=50),
            nullable=False,
            server_default="STANDARD",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "optimize_research_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.alter_column("users", "password_hash", server_default=None)
    op.alter_column("users", "role", server_default=None)
    op.alter_column("users", "default_output_mode", server_default=None)
    op.alter_column("users", "default_research_scope", server_default=None)
    op.alter_column("users", "default_research_mode", server_default=None)
    op.alter_column("users", "optimize_research_default", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "optimize_research_default")
    op.drop_column("users", "default_research_mode")
    op.drop_column("users", "default_research_scope")
    op.drop_column("users", "default_output_mode")
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")

    op.alter_column(
        "users",
        "display_name",
        existing_type=sa.String(length=120),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        type_=sa.String(length=320),
        existing_nullable=False,
    )

