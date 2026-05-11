"""add canvases, canvas_elements, canvas_connections

Revision ID: 202605102100
Revises: 202605101200
Create Date: 2026-05-10

See DATA_MODEL sections 4.9 (canvases), 4.10 (canvas_elements), 4.11 (canvas_connections).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "202605102100"
down_revision: Union[str, Sequence[str], None] = "202605101200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "canvases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'Working canvas'"),
        ),
        sa.Column(
            "viewport_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
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
    op.alter_column("canvases", "title", server_default=None)

    op.create_table(
        "canvas_elements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "canvas_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canvases.id", ondelete="CASCADE"),
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
        sa.Column("element_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=True),
        sa.Column(
            "content_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("x", sa.Numeric(), nullable=False),
        sa.Column("y", sa.Numeric(), nullable=False),
        sa.Column("width", sa.Numeric(), nullable=True),
        sa.Column("height", sa.Numeric(), nullable=True),
        sa.Column(
            "z_index",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "style_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
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
        sa.Column(
            "edited_by_user",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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
    op.alter_column("canvas_elements", "z_index", server_default=None)
    op.alter_column("canvas_elements", "edited_by_user", server_default=None)

    op.create_index("ix_canvas_elements_project_id", "canvas_elements", ["project_id"])
    op.create_index("ix_canvas_elements_canvas_id", "canvas_elements", ["canvas_id"])

    op.create_table(
        "canvas_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "canvas_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canvases.id", ondelete="CASCADE"),
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
        sa.Column(
            "from_element_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canvas_elements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_element_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canvas_elements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("connection_type", sa.String(length=40), nullable=False),
        sa.Column(
            "style_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
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


def downgrade() -> None:
    op.drop_table("canvas_connections")
    op.drop_index("ix_canvas_elements_canvas_id", table_name="canvas_elements")
    op.drop_index("ix_canvas_elements_project_id", table_name="canvas_elements")
    op.drop_table("canvas_elements")
    op.drop_table("canvases")
