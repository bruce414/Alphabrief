from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[2] == backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]

EnvironmentName = Literal["dev", "test", "prod"]


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+asyncpg://alphabrief:alphabrief@localhost:5432/alphabrief",
        validation_alias="DATABASE_URL",
    )
    secret_key: str = Field(
        default="change-me-in-dev-only",
        validation_alias="SECRET_KEY",
    )
    environment: EnvironmentName = Field(
        default="dev",
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"),
    )
    app_name: str = "Alphabrief API"
    app_debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    cors_allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "CORS_ALLOW_ORIGINS"),
    )

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, v: object) -> object:
        if isinstance(v, str):
            m = v.strip().lower()
            aliases = {
                "development": "dev",
                "local": "dev",
                "production": "prod",
                "ci": "test",
            }
            return aliases.get(m, m)
        return v

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def DATABASE_URL(self) -> str:
        """Same value as ``database_url`` (``DATABASE_URL`` env); Alembic uses this name."""
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Cached singleton for imports such as Alembic (`from app.core.config import settings`).
settings = get_settings()
