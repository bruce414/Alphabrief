"""Backfill canvases and project_memories for existing projects without rows.

Revision ID: 202605102200
Revises: 202605102120
Create Date: 2026-05-10

Data migration: each project should have exactly one Canvas and one ProjectMemory (v0.3).
"""

from typing import Sequence, Union

from alembic import op


revision: str = "202605102200"
down_revision: Union[str, Sequence[str], None] = "202605102120"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO canvases (id, project_id, user_id, title, viewport_json, metadata, created_at, updated_at)
        SELECT gen_random_uuid(), p.id, p.user_id, 'Working canvas', '{}'::jsonb, '{}'::jsonb, now(), now()
        FROM projects p
        WHERE NOT EXISTS (SELECT 1 FROM canvases c WHERE c.project_id = p.id);
        """
    )
    op.execute(
        """
        INSERT INTO project_memories (
            id,
            project_id,
            user_id,
            summary_markdown,
            entities_json,
            themes_json,
            open_questions_json,
            conclusions_json,
            last_compiled_from_activity_id,
            updated_by,
            created_at,
            updated_at
        )
        SELECT
            gen_random_uuid(),
            p.id,
            p.user_id,
            NULL,
            '[]'::jsonb,
            '[]'::jsonb,
            '[]'::jsonb,
            '[]'::jsonb,
            NULL,
            'SYSTEM',
            now(),
            now()
        FROM projects p
        WHERE NOT EXISTS (SELECT 1 FROM project_memories pm WHERE pm.project_id = p.id);
        """
    )


def downgrade() -> None:
    # Data-only migration; reverting would delete user-visible workspace rows.
    pass
