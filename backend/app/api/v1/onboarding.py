from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.onboarding import (
    ApplyDirectionRequest,
    SuggestDirectionsRequest,
    SuggestDirectionsResponse,
)
from app.schemas.project_overview import OverviewResponse, OverviewStatusResponse
from app.services.onboarding_service import OnboardingService
from app.services.project_service import ProjectCounts, ProjectService


router = APIRouter(tags=["onboarding"])


def _jsonb_str_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, str)]
    return []


def _to_overview_response(project, counts: ProjectCounts) -> OverviewResponse:
    return OverviewResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        researchGoal=project.research_goal,
        researchType=project.research_type,
        includedTopics=_jsonb_str_list(project.included_topics),
        excludedTopics=_jsonb_str_list(project.excluded_topics),
        targetEntities=_jsonb_str_list(project.target_entities),
        timeHorizon=project.time_horizon,
        createdAt=project.created_at,
        updatedAt=project.updated_at,
        status=OverviewStatusResponse(
            totalNodes=counts.canvas_element_count,
            totalSources=counts.source_count,
            openQuestionsCount=0,
            unsupportedClaimsCount=0,
            updatesAvailableCount=project.updates_available_count,
            lastCheckedAt=project.last_checked_at,
        ),
    )


@router.post(
    "/projects/{project_id}/onboarding/suggest-directions",
    response_model=SuggestDirectionsResponse,
)
async def suggest_onboarding_directions(
    project_id: UUID,
    data: SuggestDirectionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuggestDirectionsResponse:
    repo = ProjectRepository(db)
    project_svc = ProjectService(repo)
    await project_svc.get_project_or_forbidden(user=current_user, project_id=project_id)

    svc = OnboardingService(db)
    result = await svc.suggest_directions(project_id=project_id, description=data.description)
    return SuggestDirectionsResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/onboarding/apply",
    response_model=OverviewResponse,
)
async def apply_onboarding_direction(
    project_id: UUID,
    data: ApplyDirectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverviewResponse:
    repo = ProjectRepository(db)
    project_svc = ProjectService(repo)
    await project_svc.get_project_or_forbidden(user=current_user, project_id=project_id)

    svc = OnboardingService(db)
    project = await svc.apply_direction(
        user_id=current_user.id,
        project_id=project_id,
        direction=data.direction,
    )
    counts = await project_svc.counts_for_single_project(db=db, project_id=project.id)
    return _to_overview_response(project, counts)
