from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import get_settings
from app.core.security import create_session_token, session_expiry_from_now
from app.repositories.user_repository import UserRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService


router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, *, token: str, expires_at) -> None:
    settings = get_settings()

    # We set `expires` and `max_age` explicitly for broad client support.
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.environment == "prod",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        expires=expires_at,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    repo = UserRepository(db)
    svc = AuthService(repo)
    user = await svc.register(email=str(data.email), password=data.password, display_name=data.display_name)

    # Ensure every user has a Catchall project (DATA_MODEL.md §4.2).
    project_repo = ProjectRepository(db)
    project_svc = ProjectService(project_repo)
    await project_svc.ensure_catchall_for_user(user=user, db=db)

    expires_at = session_expiry_from_now()
    token = create_session_token(user_id=user.id, expires_at=expires_at)
    _set_session_cookie(response, token=token, expires_at=expires_at)
    return AuthResponse(userId=str(user.id), email=user.email, displayName=user.display_name)


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    repo = UserRepository(db)
    svc = AuthService(repo)
    user = await svc.login(email=str(data.email), password=data.password)
    expires_at = session_expiry_from_now()
    token = create_session_token(user_id=user.id, expires_at=expires_at)
    _set_session_cookie(response, token=token, expires_at=expires_at)
    return AuthResponse(userId=str(user.id), email=user.email, displayName=user.display_name)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    _clear_session_cookie(response)

