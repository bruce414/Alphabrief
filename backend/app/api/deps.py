from typing import Annotated

import httpx
from fastapi import Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import verify_session_token
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

DbSession = Annotated[AsyncSession, Depends(get_db)]

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise AppError(
            error_code="UNAUTHORIZED",
            message="Not authenticated",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    claims = verify_session_token(token)
    if claims is None:
        raise AppError(
            error_code="UNAUTHORIZED",
            message="Invalid session",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    repo = UserRepository(db)
    user = await repo.get_by_id(claims.user_id)
    if user is None:
        raise AppError(
            error_code="UNAUTHORIZED",
            message="Invalid session",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return user


async def get_http_client():
    settings = get_settings()
    timeout = httpx.Timeout(settings.fetch_timeout_seconds)
    # Avoid inheriting environment proxy vars in local/dev; those can break access
    # to YouTube (common "Tunnel connection failed: 403").
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
    ) as client:
        yield client


__all__ = [
    "DbSession",
    "get_db",
    "get_current_user",
    "get_http_client",
]
