from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Alphabrief API"
    app_env: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENV"),
    )
    app_debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    cors_allowed_origins: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "CORS_ALLOW_ORIGINS"),
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


settings = Settings()
