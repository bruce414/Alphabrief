from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    request_validation_error_handler,
)
from fastapi.exceptions import RequestValidationError

from app.core.logging import configure_logging

configure_logging()


async def _sweep_orphaned_runs() -> None:
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import update

    from app.db.session import async_session_factory
    from app.models.analysis_run import AnalysisRun
    from app.models.generation_job import GenerationJob
    from app.models.research_item import ResearchItem

    cutoff = datetime.now(UTC) - timedelta(minutes=10)
    async with async_session_factory() as db:
        await db.execute(
            update(AnalysisRun)
            .where(AnalysisRun.status == "RUNNING", AnalysisRun.updated_at < cutoff)
            .values(
                status="FAILED",
                error_code="RUN_ORPHANED",
                error_message="Worker restarted before completion.",
            )
        )
        await db.execute(
            update(GenerationJob)
            .where(
                GenerationJob.status == "RUNNING", GenerationJob.updated_at < cutoff
            )
            .values(
                status="FAILED",
                error_code="RUN_ORPHANED",
                error_message="Worker restarted before completion.",
            )
        )
        await db.execute(
            update(ResearchItem)
            .where(ResearchItem.status == "RUNNING", ResearchItem.updated_at < cutoff)
            .values(
                status="FAILED",
                error_code="RUN_ORPHANED",
                error_message="Worker restarted before completion.",
            )
        )
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _sweep_orphaned_runs()
    yield


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def root_health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
