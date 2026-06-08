"""HTTP fetch for article URLs with redirect validation and body size limits."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from fastapi import status

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.services.url_safety_service import normalize_http_url, validate_http_url_safe_for_fetch


MAX_REDIRECTS = 15


@dataclass(frozen=True)
class ArticleFetchResult:
    final_url: str
    status_code: int
    headers: dict[str, str]
    content: bytes
    content_type: str | None


async def safe_fetch_url(
    start_url: str,
    *,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> ArticleFetchResult:
    """Follow redirects manually; validate each hop for SSRF; cap body at max_fetch_bytes."""
    settings = settings or get_settings()
    timeout = httpx.Timeout(settings.fetch_timeout_seconds)
    headers = {"User-Agent": settings.http_user_agent, "Accept": "*/*"}

    own_client = client is None
    client = client or httpx.AsyncClient(timeout=timeout, follow_redirects=False)

    try:
        current = normalize_http_url(start_url)
        for _ in range(MAX_REDIRECTS):
            await validate_http_url_safe_for_fetch(current, settings=settings)

            async with client.stream(
                "GET",
                current,
                headers=headers,
                follow_redirects=False,
            ) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    loc = response.headers.get("location")
                    if not loc:
                        raise AppError(
                            error_code="SOURCE_EXTRACTION_FAILED",
                            message="Redirect without Location header",
                            status_code=status.HTTP_502_BAD_GATEWAY,
                        )
                    current = normalize_http_url(urljoin(str(response.url), loc))
                    continue

                buf = bytearray()
                async for chunk in response.aiter_bytes():
                    buf.extend(chunk)
                    if len(buf) > settings.max_fetch_bytes:
                        raise AppError(
                            error_code="SOURCE_EXTRACTION_FAILED",
                            message="Response body exceeds maximum allowed size",
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        )

                ctype = response.headers.get("content-type")
                hdrs = {k.lower(): v for k, v in response.headers.items()}
                return ArticleFetchResult(
                    final_url=str(response.url),
                    status_code=response.status_code,
                    headers=hdrs,
                    content=bytes(buf),
                    content_type=ctype.split(";")[0].strip().lower() if ctype else None,
                )

        raise AppError(
            error_code="SOURCE_EXTRACTION_FAILED",
            message="Too many redirects",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    finally:
        if own_client:
            await client.aclose()
