from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.research_item_repository import ResearchItemRepository
from app.schemas.research_item import (
    ListResearchItemsResponse,
    ResearchItemDetailResponse,
    ResearchItemListItem,
)

router = APIRouter(prefix="/research-items", tags=["research-items"])


@router.get("", response_model=ListResearchItemsResponse)
async def list_research_items(
    cursor: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListResearchItemsResponse:
    repo = ResearchItemRepository(db)
    items, next_cursor = await repo.list_by_user_cursor(
        user_id=current_user.id,
        limit=limit,
        cursor_id=cursor,
    )

    return ListResearchItemsResponse(
        items=[
            ResearchItemListItem(
                id=i.id,
                itemType=i.item_type,
                title=i.title,
                shortSummary=i.short_summary,
                status=i.status,
                analysisMode=i.analysis_mode,
                createdAt=i.created_at,
            )
            for i in items
        ],
        nextCursor=next_cursor,
    )


@router.get("/{research_item_id}", response_model=ResearchItemDetailResponse)
async def get_research_item(
    research_item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResearchItemDetailResponse:
    repo = ResearchItemRepository(db)
    item = await repo.get_by_id(research_item_id)
    if item is None:
        raise AppError(
            error_code="RESEARCH_ITEM_NOT_FOUND",
            message="Research item not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if item.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this research item",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return ResearchItemDetailResponse(
        id=item.id,
        userId=item.user_id,
        sourceId=item.source_id,
        itemType=item.item_type,
        title=item.title,
        status=item.status,
        originalUserInput=item.original_user_input,
        outputMarkdown=item.output_markdown,
        outputJson=item.output_json,
        shortSummary=item.short_summary,
        confidenceLabel=item.confidence_label,
        confidenceExplanation=item.confidence_explanation,
        analysisMode=item.analysis_mode,
        disclaimer=item.disclaimer,
        modelProvider=item.model_provider,
        modelName=item.model_name,
        promptVersion=item.prompt_version,
        requestedResearchMode=item.requested_research_mode,
        completionStrategy=item.completion_strategy,
        coverageMode=item.coverage_mode,
        analysisDepthSummary=item.analysis_depth_summary,
        generatedAt=item.generated_at,
        createdAt=item.created_at,
        updatedAt=item.updated_at,
    )

