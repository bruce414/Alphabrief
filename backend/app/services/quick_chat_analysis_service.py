from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
import trafilatura

from app.clients.ai_provider_client import get_ai_provider_client
from app.core.config import settings
from app.schemas.quick_chat import (
    ALLOWED_EDGE_LABELS,
    MarketMapBlock,
    MarketMapEdgeSchema,
    MarketMapNodeSchema,
    QuickChatAnalysisBlock,
    QuickChatAnalyzeErrorBody,
    QuickChatAnalyzeErrorResponse,
    QuickChatAnalyzeSuccessResponse,
)
from app.services.quick_chat_analysis_prompt import (
    JSON_RETRY_USER_MESSAGE,
    SYSTEM_PROMPT,
    build_user_prompt,
)

logger = logging.getLogger(__name__)

MIN_SOURCE_CHARS = 200
MAX_SOURCE_CHARS = 80_000

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = _JSON_FENCE_RE.sub("", cleaned).strip()
    return cleaned


def _parse_json_object(raw: str) -> dict[str, Any]:
    text = _strip_json_fences(raw)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Top-level JSON value must be an object")
    return parsed


def _validate_market_map(market_map: dict[str, Any]) -> MarketMapBlock:
    nodes_raw = market_map.get("nodes")
    edges_raw = market_map.get("edges")
    if not isinstance(nodes_raw, list) or not isinstance(edges_raw, list):
        raise ValueError("market_map must include nodes and edges arrays")

    node_count = len(nodes_raw)
    edge_count = len(edges_raw)
    if not (8 <= node_count <= 15):
        raise ValueError(f"market_map must have 8–15 nodes (got {node_count})")
    if not (8 <= edge_count <= 20):
        raise ValueError(f"market_map must have 8–20 edges (got {edge_count})")

    nodes = [MarketMapNodeSchema.model_validate(n) for n in nodes_raw]
    edges = [MarketMapEdgeSchema.model_validate(e) for e in edges_raw]

    node_ids = {n.id for n in nodes}
    if len(node_ids) != len(nodes):
        raise ValueError("market_map node ids must be unique")

    connected: set[str] = set()
    for edge in edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            raise ValueError("edge source/target must reference existing node ids")
        label = edge.label.strip().lower()
        if label not in ALLOWED_EDGE_LABELS:
            raise ValueError(f"invalid edge label: {edge.label!r}")
        connected.add(edge.source)
        connected.add(edge.target)

    orphan_ids = node_ids - connected
    if orphan_ids:
        raise ValueError(f"every node must appear on at least one edge; orphan ids: {sorted(orphan_ids)}")

    return MarketMapBlock(nodes=nodes, edges=edges)


def _validate_analysis(analysis: dict[str, Any]) -> QuickChatAnalysisBlock:
    block = QuickChatAnalysisBlock.model_validate(analysis)
    if not block.watch_next:
        raise ValueError("analysis.watch_next must contain at least one item")
    return block


def _validate_payload(payload: dict[str, Any]) -> QuickChatAnalyzeSuccessResponse:
    analysis_raw = payload.get("analysis")
    market_map_raw = payload.get("market_map")
    if not isinstance(analysis_raw, dict) or not isinstance(market_map_raw, dict):
        raise ValueError("payload must include analysis and market_map objects")
    analysis = _validate_analysis(analysis_raw)
    market_map = _validate_market_map(market_map_raw)
    return QuickChatAnalyzeSuccessResponse(analysis=analysis, market_map=market_map)


async def fetch_source_text_from_url(
    url: str,
    *,
    http_client: httpx.AsyncClient,
) -> tuple[str | None, QuickChatAnalyzeErrorBody | None]:
    """Fetch and extract article text. Returns (text, error) — never raises."""
    target = url.strip()
    if not target:
        return None, QuickChatAnalyzeErrorBody(
            error_code="SOURCE_FETCH_FAILED",
            message="source_url is empty",
        )

    try:
        response = await http_client.get(
            target,
            follow_redirects=True,
            headers={"User-Agent": settings.http_user_agent},
        )
        response.raise_for_status()
        html = response.content
        if not html:
            return None, QuickChatAnalyzeErrorBody(
                error_code="SOURCE_FETCH_FAILED",
                message="URL returned an empty response body",
            )
        final_url = str(response.url)
        raw_html = html.decode("utf-8", errors="replace")
        text = (trafilatura.extract(raw_html, url=final_url) or "").strip()
        if len(text) < MIN_SOURCE_CHARS:
            return None, QuickChatAnalyzeErrorBody(
                error_code="SOURCE_FETCH_FAILED",
                message=(
                    f"Could not extract enough text from URL "
                    f"(minimum {MIN_SOURCE_CHARS} characters required)"
                ),
            )
        return text[:MAX_SOURCE_CHARS], None
    except httpx.HTTPError as exc:
        logger.info("Quick chat URL fetch failed for %s: %s", target, exc)
        return None, QuickChatAnalyzeErrorBody(
            error_code="SOURCE_FETCH_FAILED",
            message=f"Could not fetch source URL: {exc}",
        )
    except Exception as exc:
        logger.warning("Quick chat URL extraction failed for %s", target, exc_info=True)
        return None, QuickChatAnalyzeErrorBody(
            error_code="SOURCE_FETCH_FAILED",
            message=f"Could not extract text from source URL: {exc}",
        )


async def _resolve_source_body(
    *,
    source_url: str | None,
    source_text: str | None,
    http_client: httpx.AsyncClient,
) -> tuple[str | None, QuickChatAnalyzeErrorBody | None]:
    text = (source_text or "").strip()
    if text:
        if len(text) < MIN_SOURCE_CHARS:
            return None, QuickChatAnalyzeErrorBody(
                error_code="SOURCE_TEXT_TOO_SHORT",
                message=(
                    f"source_text must be at least {MIN_SOURCE_CHARS} characters "
                    f"(got {len(text)})"
                ),
            )
        return text[:MAX_SOURCE_CHARS], None

    if source_url and source_url.strip():
        return await fetch_source_text_from_url(
            source_url.strip(),
            http_client=http_client,
        )

    return None, QuickChatAnalyzeErrorBody(
        error_code="SOURCE_MISSING",
        message="No usable source text or URL was provided",
    )


async def analyze_quick_chat_source(
    *,
    source_url: str | None,
    source_text: str | None,
    user_query: str | None,
    http_client: httpx.AsyncClient,
) -> QuickChatAnalyzeSuccessResponse | QuickChatAnalyzeErrorResponse:
    body, fetch_error = await _resolve_source_body(
        source_url=source_url,
        source_text=source_text,
        http_client=http_client,
    )
    if fetch_error is not None:
        return QuickChatAnalyzeErrorResponse(error=fetch_error)

    assert body is not None
    user_prompt = build_user_prompt(
        source_body=body,
        user_query=user_query,
        source_url=source_url,
    )

    ai_client = get_ai_provider_client()
    prior_raw: str | None = None
    last_error: str | None = None

    for attempt in range(2):
        try:
            if attempt == 0:
                raw = await ai_client.generate_quick_chat_analysis_json(
                    system=SYSTEM_PROMPT,
                    user_content=user_prompt,
                )
            else:
                raw = await ai_client.generate_quick_chat_analysis_json(
                    system=SYSTEM_PROMPT,
                    user_content=user_prompt,
                    prior_assistant_content=prior_raw or "",
                    follow_up_user_content=JSON_RETRY_USER_MESSAGE,
                )
            prior_raw = raw
            payload = _parse_json_object(raw)
            return _validate_payload(payload)
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = str(exc)
            logger.info(
                "Quick chat analysis parse/validate failed (attempt %s): %s",
                attempt + 1,
                exc,
            )
            continue
        except Exception:
            logger.exception("Quick chat analysis generation failed")
            return QuickChatAnalyzeErrorResponse(
                error=QuickChatAnalyzeErrorBody(
                    error_code="ANALYSIS_FAILED",
                    message="Could not generate source analysis",
                )
            )

    return QuickChatAnalyzeErrorResponse(
        error=QuickChatAnalyzeErrorBody(
            error_code="ANALYSIS_INVALID_JSON",
            message=last_error or "Model response was not valid analysis JSON",
        )
    )
