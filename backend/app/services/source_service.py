from __future__ import annotations

import logging

import httpx
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.youtube_client import parse_youtube_video_id
from app.core.errors import AppError
from app.models.source import Source
from app.models.user import User
from app.repositories.source_repository import SourceRepository
from app.schemas.source import CreateSourceRequest
from app.services.input_detection_service import classify_url_input_type
from app.services.source_extraction_service import (
    apply_article_extraction,
    apply_youtube_extraction,
)
from app.services.url_safety_service import assert_url_scheme_http
from app.services.usage_tracking_service import record_source_extraction_event

logger = logging.getLogger(__name__)


async def create_source_from_request(
    *,
    db: AsyncSession,
    current_user: User,
    data: CreateSourceRequest,
    http_client: httpx.AsyncClient,
) -> Source:
    inp = data.input.strip()
    st = data.source_type
    project_id = data.project_id

    if st == "AUTO_DETECT":
        resolved = classify_url_input_type(inp).value
        if resolved not in {"ARTICLE_URL", "YOUTUBE_URL", "FILING_URL"}:
            raise AppError(
                error_code="INVALID_URL",
                message="Could not classify URL",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        st_resolved: str = resolved
    else:
        st_resolved = st

    if st_resolved in {"ARTICLE_URL", "FILING_URL"}:
        assert_url_scheme_http(inp)
        access_method = "SERVER_FETCH"
    else:
        if not parse_youtube_video_id(inp):
            raise AppError(
                error_code="INVALID_URL",
                message="Not a valid YouTube URL",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        access_method = "YOUTUBE_METADATA"

    source = Source(
        user_id=current_user.id,
        project_id=project_id,
        source_type=st_resolved,
        source_access_method=access_method,
        source_access_status="PENDING",
        original_input=inp,
        normalized_url=None,
        raw_text_retention="NOT_STORED",
        metadata_={},
    )

    repo = SourceRepository(db)
    await repo.create(source)

    try:
        if st_resolved in {"ARTICLE_URL", "FILING_URL"}:
            await apply_article_extraction(source, db=db, http_client=http_client)
        else:
            await apply_youtube_extraction(source, http_client=http_client)
    except AppError as exc:
        if exc.error_code == "SOURCE_BLOCKED":
            source.source_access_status = "BLOCKED"
            source.extraction_error = exc.message
            await repo.update(source)
            await record_source_extraction_event(
                db, user_id=current_user.id, source_id=source.id
            )
        elif exc.error_code == "SOURCE_EXTRACTION_FAILED":
            source.source_access_status = "FAILED"
            source.extraction_error = exc.message
            await repo.update(source)
            await record_source_extraction_event(
                db, user_id=current_user.id, source_id=source.id
            )
        raise
    except httpx.HTTPError as exc:
        logger.warning("HTTP error during source extraction", exc_info=exc)
        source.source_access_status = "FAILED"
        source.extraction_error = "Network error during fetch"
        await repo.update(source)
        await record_source_extraction_event(
            db, user_id=current_user.id, source_id=source.id
        )
        raise AppError(
            error_code="SOURCE_EXTRACTION_FAILED",
            message="Could not retrieve source content",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during source extraction")
        source.source_access_status = "FAILED"
        source.extraction_error = "Unexpected extraction error"
        await repo.update(source)
        await record_source_extraction_event(
            db, user_id=current_user.id, source_id=source.id
        )
        raise AppError(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    await repo.update(source)
    await record_source_extraction_event(
        db, user_id=current_user.id, source_id=source.id
    )
    return source
