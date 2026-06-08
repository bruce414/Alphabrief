from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_http_client
from app.models.user import User
from app.schemas.quick_chat import (
    QuickChatAnalyzeErrorResponse,
    QuickChatAnalyzeRequest,
    QuickChatAnalyzeSuccessResponse,
)
from app.services.quick_chat_analysis_service import analyze_quick_chat_source

router = APIRouter(prefix="/quick-chat", tags=["quick_chat"])


@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    response_model=QuickChatAnalyzeSuccessResponse | QuickChatAnalyzeErrorResponse,
)
async def analyze_quick_chat(
    data: QuickChatAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> QuickChatAnalyzeSuccessResponse | QuickChatAnalyzeErrorResponse:
    _ = current_user
    return await analyze_quick_chat_source(
        source_url=data.source_url,
        source_text=data.source_text,
        user_query=data.user_query,
        http_client=http_client,
    )
