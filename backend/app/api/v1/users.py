from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdateRequest


router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def patch_me(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    if data.display_name is not None:
        current_user.display_name = data.display_name
    if data.default_output_mode is not None:
        current_user.default_output_mode = data.default_output_mode
    if data.default_research_scope is not None:
        current_user.default_research_scope = data.default_research_scope.value
    if data.default_research_mode is not None:
        current_user.default_research_mode = data.default_research_mode.value
    if data.optimize_research_default is not None:
        current_user.optimize_research_default = data.optimize_research_default

    repo = UserRepository(db)
    updated = await repo.update(current_user)
    return UserResponse.model_validate(updated)

