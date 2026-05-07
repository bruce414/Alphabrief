from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_event import UsageEvent


async def record_segment_analysis_usage(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    research_item_id: uuid.UUID,
    source_id: uuid.UUID | None,
    input_tokens: int,
    output_tokens: int,
    allowance_percent: Decimal | None,
) -> None:
    """Persist token usage for one analyzed segment (schema has input/output only)."""

    db.add(
        UsageEvent(
            user_id=user_id,
            research_item_id=research_item_id,
            source_id=source_id,
            event_type="SEGMENT_ANALYSIS",
            model_provider="mock",
            model_name="mock-segment",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_allowance_impact_percent=allowance_percent,
            actual_allowance_impact_percent=None,
            internal_cost_score=None,
            estimated_cost_usd=None,
        )
    )


async def record_source_extraction_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    source_id: uuid.UUID,
) -> None:
    db.add(
        UsageEvent(
            user_id=user_id,
            source_id=source_id,
            research_item_id=None,
            event_type="SOURCE_EXTRACTION",
            model_provider=None,
            model_name=None,
            input_tokens=None,
            output_tokens=None,
            estimated_allowance_impact_percent=None,
            actual_allowance_impact_percent=None,
            internal_cost_score=None,
            estimated_cost_usd=None,
        )
    )
    await db.commit()
