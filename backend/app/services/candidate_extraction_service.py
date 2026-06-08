from __future__ import annotations

import logging
from typing import Callable
from uuid import UUID

import bleach
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_provider_client import AiProviderClient, get_ai_provider_client
from app.core.enums import CandidateStatus, CanvasElementType
from app.db.session import async_session_factory
from app.models.canvas_element import CanvasElement
from app.models.candidate_element import CandidateElement
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.chat_turn_source import ChatTurnSource
from app.models.project import Project
from app.models.source import Source
from app.models.usage_event import UsageEvent


logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AsyncSession]

_ALLOWED_EXTRACTION_KINDS = frozenset(
    {
        CanvasElementType.CLAIM.value,
        CanvasElementType.RISK.value,
        CanvasElementType.EVIDENCE.value,
        CanvasElementType.QUESTION.value,
    }
)
_MAX_CANDIDATES_PER_TURN = 2
_ALLOWED_PROPOSAL_EDGE_TYPES = frozenset({"supports", "contradicts", "affects"})


ALLOWED_TAGS = [
    "p",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "h2",
    "h3",
    "code",
    "blockquote",
    "a",
]


def _normalize_title(title: str) -> str:
    return " ".join((title or "").strip().lower().split())


async def _existing_canvas_context(
    db: AsyncSession,
    project_id: UUID,
) -> tuple[dict[str, UUID], list[dict[str, str]]]:
    rows = (
        await db.execute(
            select(CanvasElement.id, CanvasElement.title, CanvasElement.element_type).where(
                CanvasElement.project_id == project_id,
                CanvasElement.title.is_not(None),
                CanvasElement.archived_at.is_(None),
            )
        )
    ).all()
    title_map: dict[str, UUID] = {}
    elements: list[dict[str, str]] = []
    for el_id, title, element_type in rows:
        if isinstance(title, str) and title.strip():
            title_map[_normalize_title(title)] = el_id
            elements.append(
                {
                    "title": title.strip(),
                    "element_type": str(element_type or "").strip(),
                }
            )
    return title_map, elements


def _format_existing_elements_for_prompt(elements: list[dict[str, str]]) -> str:
    if not elements:
        return "Existing canvas elements: (none — omit proposed_edge)\n\n"
    lines = [
        "Existing canvas elements (proposed_edge.target_title must match one of these titles exactly):"
    ]
    for el in elements[:40]:
        et = el.get("element_type") or "TEXT"
        lines.append(f'- [{et}] {el.get("title", "")}')
    return "\n".join(lines) + "\n\n"


def _resolve_proposed_edges(
    candidates: list[dict],
    *,
    title_map: dict[str, UUID],
) -> list[dict]:
    resolved: list[dict] = []
    for candidate in candidates:
        proposed = candidate.get("proposed_edge")
        if not isinstance(proposed, dict):
            resolved.append(candidate)
            continue

        edge_type = str(proposed.get("edge_type") or "").strip().lower()
        target_title_raw = proposed.get("target_title")
        target_title = (
            target_title_raw.strip()
            if isinstance(target_title_raw, str) and target_title_raw.strip()
            else ""
        )
        if edge_type not in _ALLOWED_PROPOSAL_EDGE_TYPES or not target_title:
            resolved.append(candidate)
            continue

        target_element_id = title_map.get(_normalize_title(target_title))
        if target_element_id is None:
            resolved.append(candidate)
            continue

        out = dict(candidate)
        out["resolved_proposed_edge"] = {
            "edge_type": edge_type,
            "target_element_id": str(target_element_id),
            "target_title": target_title,
        }
        resolved.append(out)
    return resolved


def _postprocess_extracted_candidates(
    extracted: list[dict],
    *,
    existing_title_keys: set[str],
) -> list[dict]:
    """Filter kinds, cap count, and dedupe by normalized title against canvas elements."""
    filtered: list[dict] = []
    for raw in extracted:
        if not isinstance(raw, dict):
            continue
        kind = (
            raw.get("kind")
            or raw.get("suggested_element_type")
            or ""
        )
        kind = str(kind).strip().upper()
        if kind not in _ALLOWED_EXTRACTION_KINDS:
            continue
        body = (raw.get("body") or raw.get("content_markdown") or "").strip()
        if not body:
            continue
        title_raw = raw.get("title")
        title = (
            title_raw.strip()[:500]
            if isinstance(title_raw, str) and title_raw.strip()
            else None
        )
        item: dict = {
            "suggested_element_type": kind,
            "title": title,
            "content_markdown": body,
            "suggested_position": raw.get("suggested_position"),
        }
        proposed_edge = raw.get("proposed_edge")
        if isinstance(proposed_edge, dict):
            item["proposed_edge"] = proposed_edge
        filtered.append(item)

    capped = filtered[:_MAX_CANDIDATES_PER_TURN]

    survivors: list[dict] = []
    for candidate in capped:
        title = candidate.get("title")
        if isinstance(title, str) and title.strip():
            key = _normalize_title(title)
            if key in existing_title_keys:
                logger.debug(
                    "Dropping candidate with duplicate title %r (normalized %r)",
                    title,
                    key,
                )
                continue
        survivors.append(candidate)
    return survivors


async def extract_candidates_for_turn_safe(
    asst_turn_id: UUID,
    *,
    session_factory: SessionFactory = async_session_factory,
    ai_provider: AiProviderClient | None = None,
) -> None:
    """Top-level Phase 2 entry. Never raises."""
    try:
        async with session_factory() as db:
            # Tests run everything inside a connection-scoped nested transaction.
            # Opening a second session on the same connection must create its own savepoint.
            await db.begin_nested()
            await _extract(asst_turn_id=asst_turn_id, db=db, ai_provider=ai_provider)
    except Exception:
        logger.exception("Candidate extraction failed for %s; skipping.", asst_turn_id)


async def extract_candidates_for_turn_in_session_safe(
    asst_turn_id: UUID,
    *,
    db: AsyncSession,
    ai_provider: AiProviderClient | None = None,
) -> None:
    """Best-effort extraction using an existing session. Never raises."""
    try:
        await _extract(asst_turn_id=asst_turn_id, db=db, ai_provider=ai_provider)
    except Exception:
        logger.exception("Candidate extraction failed for %s; skipping.", asst_turn_id)


async def _extract(*, asst_turn_id: UUID, db: AsyncSession, ai_provider: AiProviderClient | None) -> None:
    # Load assistant turn.
    asst = (await db.execute(select(ChatTurn).where(ChatTurn.id == asst_turn_id))).scalar_one_or_none()
    if asst is None:
        return
    if not (asst.content_markdown or "").strip():
        return

    # Load chat + project.
    chat = (await db.execute(select(Chat).where(Chat.id == asst.chat_id))).scalar_one()
    project = (await db.execute(select(Project).where(Project.id == chat.project_id))).scalar_one()
    _ = project  # soft-mode for CATCHALL: we still run extraction

    # Load user message: previous user turn in the same chat.
    user_turn = (
        await db.execute(
            select(ChatTurn).where(
                ChatTurn.chat_id == asst.chat_id,
                ChatTurn.turn_index == asst.turn_index - 1,
            )
        )
    ).scalar_one_or_none()
    user_message = (user_turn.content_markdown if user_turn is not None else "") or ""

    # Load attached sources from user turn.
    sources: list[Source] = []
    if user_turn is not None:
        rows = list(
            (
                await db.execute(select(ChatTurnSource).where(ChatTurnSource.chat_turn_id == user_turn.id))
            )
            .scalars()
            .all()
        )
        source_ids = [r.source_id for r in rows]
        if source_ids:
            sources = list(
                (
                    await db.execute(select(Source).where(Source.id.in_(source_ids)))
                )
                .scalars()
                .all()
            )

    ai = ai_provider or get_ai_provider_client()
    title_map, existing_elements = await _existing_canvas_context(db, chat.project_id)

    extracted = await ai.extract_candidates(
        user_message=user_message,
        assistant_reply=asst.content_markdown or "",
        attached_sources=sources,
        existing_canvas_elements=existing_elements,
    )
    candidates = _postprocess_extracted_candidates(
        extracted,
        existing_title_keys=set(title_map.keys()),
    )
    candidates = _resolve_proposed_edges(candidates, title_map=title_map)

    created_count = 0
    for c in candidates:
        element_type_raw = (c.get("suggested_element_type") or "").strip()
        content_raw = (c.get("content_markdown") or "").strip()
        title_raw = c.get("title")
        title = title_raw.strip()[:500] if isinstance(title_raw, str) and title_raw.strip() else None

        if not content_raw:
            continue
        try:
            element_type = CanvasElementType(element_type_raw)
        except Exception:
            continue

        cleaned = bleach.clean(
            content_raw,
            tags=ALLOWED_TAGS,
            attributes={"a": ["href", "title"]},
            strip=True,
        ).strip()
        if not cleaned:
            continue

        content_json: dict = {}
        suggested_position = c.get("suggested_position")
        if isinstance(suggested_position, dict):
            sanitized_position: dict[str, float] = {}
            for key in ("x", "y", "width", "height"):
                value = suggested_position.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    sanitized_position[key] = float(value)
            if sanitized_position:
                content_json["suggested_position"] = sanitized_position

        resolved_edge = c.get("resolved_proposed_edge")
        if isinstance(resolved_edge, dict):
            content_json["proposed_edge"] = resolved_edge

        db.add(
            CandidateElement(
                chat_turn_id=asst.id,
                project_id=chat.project_id,
                user_id=asst.user_id,
                suggested_element_type=element_type.value,
                title=title,
                content_markdown=cleaned,
                content_json=content_json,
                status=CandidateStatus.PENDING.value,
                promoted_element_id=None,
                extraction_model_name=getattr(asst, "model_name", None),
            )
        )
        created_count += 1

    # Best-effort usage record (old UsageEvent schema).
    if created_count > 0:
        db.add(
            UsageEvent(
                user_id=asst.user_id,
                source_id=None,
                event_type="CANDIDATE_EXTRACTION",
                model_provider=asst.model_provider,
                model_name=asst.model_name,
                input_tokens=None,
                output_tokens=None,
                estimated_allowance_impact_percent=None,
                actual_allowance_impact_percent=None,
                internal_cost_score=None,
                estimated_cost_usd=None,
            )
        )

    await db.commit()

