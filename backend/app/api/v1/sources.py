from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_http_client
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.repositories.source_repository import SourceRepository
from app.schemas.source import CreateSourceRequest, SourceCreateResponse, SourceDetailResponse
from app.schemas.source_scan import RunSourceScanRequest, RunSourceScanResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.source_scan_service import run_source_scan
from app.services.source_service import create_source_from_request

router = APIRouter(prefix="/sources", tags=["sources"])


def _to_create_response(src) -> SourceCreateResponse:
    return SourceCreateResponse(
        sourceId=src.id,
        sourceType=src.source_type,
        sourceAccessMethod=src.source_access_method,
        sourceAccessStatus=src.source_access_status,
        normalizedUrl=src.normalized_url,
        canonicalUrl=src.canonical_url,
        title=src.title,
        publisher=src.publisher,
        extractedTextWordCount=src.extracted_text_word_count,
        extractionConfidence=src.extraction_confidence,
    )


def _to_detail_response(src) -> SourceDetailResponse:
    return SourceDetailResponse(
        id=src.id,
        sourceType=src.source_type,
        sourceAccessMethod=src.source_access_method,
        sourceAccessStatus=src.source_access_status,
        originalInput=src.original_input,
        normalizedUrl=src.normalized_url,
        canonicalUrl=src.canonical_url,
        title=src.title,
        publisher=src.publisher,
        author=src.author,
        publishedAt=src.published_at,
        extractedText=src.extracted_text,
        extractedTextWordCount=src.extracted_text_word_count,
        extractionConfidence=src.extraction_confidence,
        extractionError=src.extraction_error,
        rawTextRetention=src.raw_text_retention,
        contentHash=src.content_hash,
        metadata=src.metadata_,
        createdAt=src.created_at,
        updatedAt=src.updated_at,
    )


@router.post(
    "",
    response_model=SourceCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_source(
    data: CreateSourceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> SourceCreateResponse:
    src = await create_source_from_request(
        db=db,
        current_user=current_user,
        data=data,
        http_client=http_client,
    )
    return _to_create_response(src)


@router.get("/{source_id}", response_model=SourceDetailResponse)
async def get_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SourceDetailResponse:
    repo = SourceRepository(db)
    src = await repo.get_by_id(source_id)
    if src is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Source not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if src.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this source",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return _to_detail_response(src)


@router.post(
    "/{source_id}/scan",
    response_model=RunSourceScanResponse,
    status_code=status.HTTP_200_OK,
)
async def run_scan(
    source_id: UUID,
    data: RunSourceScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> RunSourceScanResponse:
    return await run_source_scan(
        db=db,
        current_user=current_user,
        source_id=source_id,
        request=data,
        http_client=http_client,
    )
