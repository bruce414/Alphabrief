from __future__ import annotations

from fastapi import status

from app.core.errors import AppError
from app.core.enums import ResearchMode, ResearchScope
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def register(self, *, email: str, password: str, display_name: str | None) -> User:
        existing = await self._repo.get_by_email(email)
        if existing is not None:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Email already registered",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            role="USER",
            default_output_mode="ASK",
            default_research_scope=ResearchScope.RECOMMENDED_CONTEXT.value,
            default_research_mode=ResearchMode.STANDARD.value,
            optimize_research_default=True,
        )
        return await self._repo.create(user)

    async def login(self, *, email: str, password: str) -> User:
        user = await self._repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AppError(
                error_code="UNAUTHORIZED",
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return user

