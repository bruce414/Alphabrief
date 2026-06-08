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
    session_cookie_name: str = Field(
        default="ab_session",
        validation_alias=AliasChoices("SESSION_COOKIE_NAME", "AUTH_COOKIE_NAME"),
    )
    http_user_agent: str = Field(
        default="AlphaBrief/0.3 (+https://alphabrief.example)",
        validation_alias="HTTP_USER_AGENT",
    )
    scraping_user_agent: str = Field(
        default="AlphaBriefBot/0.1 (+https://alphabrief.com/bot; user-initiated single-fetch)",
        validation_alias="SCRAPING_USER_AGENT",
    )
    max_fetch_bytes: int = Field(default=5 * 1024 * 1024, validation_alias="MAX_FETCH_BYTES")
    fetch_timeout_seconds: float = Field(default=30.0, validation_alias="FETCH_TIMEOUT_SECONDS")
    # Comma-separated domain suffixes (case-insensitive), e.g. ".mil"
    source_domain_denylist: str = Field(default=".mil", validation_alias="SOURCE_DOMAIN_DENYLIST")
    robots_cache_ttl_hours: int = Field(default=24, validation_alias="ROBOTS_CACHE_TTL_HOURS")
    robots_failure_ttl_hours: int = Field(default=1, validation_alias="ROBOTS_FAILURE_TTL_HOURS")
    robots_timeout_seconds: float = Field(default=5.0, validation_alias="ROBOTS_TIMEOUT_SECONDS")
    robots_max_bytes: int = Field(default=100 * 1024, validation_alias="ROBOTS_MAX_BYTES")
    source_fetch_rate_limit_per_minute: int = Field(
        default=6, validation_alias="SOURCE_FETCH_RATE_LIMIT_PER_MINUTE"
    )
    source_fetch_rate_limit_burst: int = Field(
        default=2, validation_alias="SOURCE_FETCH_RATE_LIMIT_BURST"
    )
    # Token budget assumed for a single research run when computing the
    # estimated_allowance_impact_percent before persistent allowance/cooldown
    # exists (AI_PIPELINE §17.4). Tune later once usage telemetry catches up.
    single_run_token_budget: int = Field(
        default=200_000, validation_alias="SINGLE_RUN_TOKEN_BUDGET"
    )
    # Source-enrichment fallback (AI_PIPELINE §17.1). EDGAR is the only adapter
    # in the v0.3 first slice; Wikipedia / FRED / IR-page adapters land later.
    edgar_base_url: str = Field(
        default="https://www.sec.gov", validation_alias="EDGAR_BASE_URL"
    )
    enrichment_timeout_seconds: float = Field(
        default=8.0, validation_alias="ENRICHMENT_TIMEOUT_SECONDS"
    )

    ai_provider: str = Field(default="mock", validation_alias="AI_PROVIDER")
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-sonnet-4-6",
        validation_alias="ANTHROPIC_MODEL",
    )
    # Max output tokens for a single assistant chat reply (was 2048; too small for long briefs).
    chat_max_output_tokens: int = Field(
        default=16_384,
        validation_alias="CHAT_MAX_OUTPUT_TOKENS",
    )
    # Total characters (system + history + sources + user) sent to the model per turn.
    chat_prompt_max_chars: int = Field(
        default=200_000,
        validation_alias="CHAT_PROMPT_MAX_CHARS",
    )
    onboarding_use_mock: bool = Field(default=False, validation_alias="ONBOARDING_USE_MOCK")

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

    def source_domain_denylist_suffixes(self) -> list[str]:
        parts = [p.strip().lower() for p in self.source_domain_denylist.split(",")]
        return [p for p in parts if p]

    @property
    def DATABASE_URL(self) -> str:
        """Same value as ``database_url`` (``DATABASE_URL`` env); Alembic uses this name."""
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Cached singleton for imports such as Alembic (`from app.core.config import settings`).
settings = get_settings()
