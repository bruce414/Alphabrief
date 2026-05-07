from __future__ import annotations

from fastapi import APIRouter

from app.core.enums import (
    AnalysisIntent,
    CompletionStrategy,
    CoverageMode,
    ResearchMode,
    ResearchScope,
)
from app.schemas.research_scope import ResearchScopesResponse

router = APIRouter(tags=["research-scopes"])


@router.get("/research-scopes", response_model=ResearchScopesResponse)
async def get_research_scopes() -> ResearchScopesResponse:
    return ResearchScopesResponse(
        researchScopes=[s.value for s in ResearchScope],
        researchModes=[s.value for s in ResearchMode],
        completionStrategies=[s.value for s in CompletionStrategy],
        coverageModes=[s.value for s in CoverageMode],
        analysisIntents=[s.value for s in AnalysisIntent],
    )

