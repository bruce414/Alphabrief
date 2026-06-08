"""Article and YouTube source ingestion (no scan / analysis)."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

import httpx
import trafilatura
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.services.scraping_policy import fetch_with_policy
from app.clients.youtube_client import fetch_oembed, fetch_transcript_text, parse_youtube_video_id
from app.core.config import get_settings
from app.core.errors import AppError
from app.models.source import Source


def _word_count(text: str | None) -> int:
    if not text:
        return 0
    return len(text.split())


def _metadata_to_dict(meta: object | None) -> dict[str, Any]:
    """Serialize trafilatura metadata to JSON-safe primitives only."""
    if meta is None:
        return {}
    out: dict[str, Any] = {}
    for name in (
        "title",
        "sitename",
        "author",
        "hostname",
        "description",
        "date",
    ):
        val = getattr(meta, name, None)
        if val is None:
            continue
        if hasattr(val, "isoformat"):
            out[name] = val.isoformat()
        elif isinstance(val, (str, int, float, bool)):
            out[name] = val
        else:
            out[name] = str(val)
    return out


def _extract_article_core(html: bytes, final_url: str) -> tuple[str, dict[str, Any]]:
    raw = html.decode("utf-8", errors="replace")
    text = trafilatura.extract(raw, url=final_url) or ""
    meta_obj = trafilatura.extract_metadata(raw, default_url=final_url)
    meta_dict = _metadata_to_dict(meta_obj)
    meta_dict["final_url"] = final_url
    return text, meta_dict


async def apply_article_extraction(
    source: Source,
    *,
    db: AsyncSession,
    http_client: httpx.AsyncClient | None = None,
) -> None:
    settings = get_settings()
    fetch = await fetch_with_policy(
        source.original_input,
        db=db,
        user_id=source.user_id,
        source_id=source.id,
        http_client=http_client,
    )

    source.normalized_url = fetch.final_url
    # Publisher's own declaration of where the content lives — preferred citation
    # target, especially for aggregator-hosted articles. None if not present.
    source.canonical_url = fetch.canonical_url

    # Pre-fetch policy blocks or robots metadata-only: no page body is available and must not be fetched.
    if fetch.decision.value == "BLOCKED":
        raise AppError(
            error_code="SOURCE_BLOCKED",
            message=f"Blocked by fetch policy: {fetch.reason}",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"policyReason": fetch.reason},
        )

    if fetch.decision.value == "METADATA_ONLY" and fetch.content is None:
        source.source_access_status = "METADATA_ONLY"
        source.extraction_confidence = "LOW"
        source.extracted_text = None
        source.extracted_text_word_count = None
        source.raw_text_retention = "NOT_STORED"
        source.metadata_ = {"policyDecision": fetch.decision, "policyReason": fetch.reason, "finalUrl": fetch.final_url}
        return

    html = fetch.content or b""
    source.content_hash = hashlib.sha256(html).hexdigest()

    meta_bundle: dict[str, Any] = {
        "fetchStatusCode": fetch.status_code,
        "contentType": fetch.content_type,
        "finalUrl": fetch.final_url,
        "policyDecision": fetch.decision,
        "policyReason": fetch.reason,
    }

    sc = fetch.status_code or 0
    ctype = (fetch.content_type or "").lower()

    # Post-fetch policy gates (noai / paywall / fetch_failed / unsupported content type / etc).
    # In these cases we may still have an HTML body, but we must not treat it as full-text extracted.
    if fetch.decision.value == "METADATA_ONLY":
        text, tm = _extract_article_core(html, fetch.final_url)
        meta_bundle.update(tm)
        source.title = source.title or tm.get("title")
        source.publisher = source.publisher or tm.get("sitename")
        source.author = source.author or tm.get("author")
        source.source_access_status = "METADATA_ONLY"
        source.extraction_confidence = "LOW"
        source.extracted_text = None
        source.extracted_text_word_count = _word_count(text)
        source.raw_text_retention = "NOT_STORED"
        source.metadata_ = meta_bundle
        return

    # Paywall / auth-style responses → metadata-only path
    if sc in (401, 402, 403):
        text, tm = _extract_article_core(html, fetch.final_url)
        meta_bundle.update(tm)
        source.title = source.title or (tm.get("title") if tm else None)
        source.publisher = source.publisher or tm.get("sitename")
        source.author = source.author or tm.get("author")
        source.source_access_status = "METADATA_ONLY"
        source.extraction_confidence = "LOW"
        source.extracted_text = None
        source.extracted_text_word_count = _word_count(text)
        source.raw_text_retention = "NOT_STORED"
        source.metadata_ = meta_bundle
        return

    if sc >= 400:
        if sc == 404 or sc >= 500:
            source.source_access_status = "FAILED"
            source.extraction_error = f"HTTP {sc}"
            source.extraction_confidence = "UNKNOWN"
            source.extracted_text = None
            source.extracted_text_word_count = None
            source.raw_text_retention = "NOT_STORED"
            source.metadata_ = meta_bundle
            return
        text, tm = _extract_article_core(html, fetch.final_url)
        meta_bundle.update(tm)
        source.title = source.title or tm.get("title")
        source.publisher = tm.get("sitename")
        source.author = tm.get("author")
        source.source_access_status = "METADATA_ONLY"
        source.extraction_confidence = "LOW"
        source.extracted_text = None
        source.extracted_text_word_count = _word_count(text)
        source.raw_text_retention = "NOT_STORED"
        source.metadata_ = meta_bundle
        return

    if "html" not in ctype and ctype:
        text, tm = _extract_article_core(html, fetch.final_url)
        meta_bundle.update(tm)
        source.title = source.title or tm.get("title")
        source.publisher = tm.get("sitename")
        source.source_access_status = "METADATA_ONLY"
        source.extraction_confidence = "LOW"
        source.extracted_text = None
        source.extracted_text_word_count = _word_count(text)
        source.raw_text_retention = "NOT_STORED"
        source.metadata_ = meta_bundle
        return

    text, tm = _extract_article_core(html, fetch.final_url)
    meta_bundle.update(tm)
    wc = _word_count(text)

    source.title = tm.get("title")
    source.publisher = tm.get("sitename")
    source.author = tm.get("author")
    date_val = tm.get("date")
    if isinstance(date_val, datetime):
        source.published_at = date_val
    elif isinstance(date_val, str):
        source.published_at = None
        meta_bundle["publishedDateRaw"] = date_val

    if wc >= 200:
        source.source_access_status = "FULL_TEXT_EXTRACTED"
        source.extraction_confidence = "HIGH" if wc >= 400 else "MEDIUM"
        source.extracted_text = text
        source.extracted_text_word_count = wc
        source.raw_text_retention = "EPHEMERAL"
    elif wc >= 50:
        source.source_access_status = "FULL_TEXT_EXTRACTED"
        source.extraction_confidence = "LOW"
        source.extracted_text = text
        source.extracted_text_word_count = wc
        source.raw_text_retention = "EPHEMERAL"
    else:
        source.source_access_status = "METADATA_ONLY"
        source.extraction_confidence = "LOW"
        source.extracted_text = None
        source.extracted_text_word_count = wc
        source.raw_text_retention = "NOT_STORED"

    source.metadata_ = meta_bundle


async def apply_youtube_extraction(
    source: Source,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> None:
    vid = parse_youtube_video_id(source.original_input)
    if not vid:
        source.source_access_status = "FAILED"
        source.extraction_error = "Could not parse YouTube video id"
        source.raw_text_retention = "NOT_STORED"
        source.metadata_ = {}
        return

    source.normalized_url = source.original_input.strip()

    oembed = await fetch_oembed(source.original_input.strip(), client=http_client)
    meta: dict[str, Any] = dict(oembed)
    meta["videoId"] = vid

    source.title = oembed.get("title")
    source.publisher = oembed.get("author_name")
    source.author = oembed.get("author_name")

    transcript = await fetch_transcript_text(vid)
    wc = _word_count(transcript)

    if transcript:
        source.source_access_method = "YOUTUBE_TRANSCRIPT"
        source.source_access_status = "FULL_TEXT_EXTRACTED"
        source.extraction_confidence = "HIGH" if wc >= 200 else "MEDIUM"
        # v0.3: store transcript text when available (later PRs may clear it per retention policy).
        source.extracted_text = transcript
        source.extracted_text_word_count = wc
        source.raw_text_retention = "EPHEMERAL"
        meta["transcriptPreviewChars"] = min(len(transcript), 500)
        source.metadata_ = meta
        return

    source.source_access_method = "YOUTUBE_METADATA"
    source.source_access_status = "METADATA_ONLY"
    source.extraction_confidence = "LOW"
    source.extracted_text = None
    source.extracted_text_word_count = None
    source.raw_text_retention = "NOT_STORED"
    source.metadata_ = meta
