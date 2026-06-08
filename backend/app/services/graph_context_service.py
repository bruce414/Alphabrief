from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CanvasElementType, ConnectionType
from app.models.canvas_connection import CanvasConnection
from app.models.canvas_element import CanvasElement
from app.repositories.canvas_connection_repository import CanvasConnectionRepository
from app.repositories.canvas_element_repository import CanvasElementRepository

_QUERY_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "what",
        "how",
        "why",
        "does",
        "this",
        "that",
        "with",
        "from",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "can",
        "could",
        "should",
        "would",
        "will",
        "about",
        "into",
        "your",
        "you",
        "our",
        "their",
        "its",
        "not",
        "but",
        "all",
        "any",
        "who",
        "which",
        "when",
        "where",
        "there",
        "here",
        "than",
        "then",
        "them",
        "they",
        "she",
        "him",
        "her",
        "his",
        "been",
        "being",
        "also",
        "just",
        "only",
        "more",
        "most",
        "some",
        "such",
        "other",
        "each",
        "tell",
        "show",
        "give",
        "find",
    }
)

_EXCERPT_MAX_CHARS = 140
_TOKEN_CHAR_RATIO = 4


@dataclass(frozen=True, slots=True)
class GraphContextResult:
    markdown: str | None
    node_count: int | None


def _tokenize_user_message(user_message: str) -> list[str]:
    lowered = user_message.lower()
    cleaned = re.sub(r"[^\w\s]", " ", lowered)
    tokens: list[str] = []
    for raw in cleaned.split():
        token = raw.strip()
        if len(token) < 3:
            continue
        if token in _QUERY_STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _element_search_text(element: CanvasElement) -> str:
    title = (element.title or "").strip()
    body = (element.content_markdown or "").strip()
    return f"{title} {body}".strip()


def _score_element(element: CanvasElement, query_tokens: list[str]) -> int:
    if not query_tokens:
        return 0
    haystack = _element_search_text(element).lower()
    if not haystack:
        return 0
    return sum(1 for token in query_tokens if token in haystack)


def _excerpt(content_markdown: str | None) -> str:
    text = (content_markdown or "").strip().replace("\n", " ")
    if len(text) <= _EXCERPT_MAX_CHARS:
        return text
    return text[:_EXCERPT_MAX_CHARS].rstrip() + "…"


def _edge_label(connection_type: str) -> str:
    try:
        return ConnectionType(connection_type).value.lower().replace("_", " ")
    except ValueError:
        return connection_type.lower().replace("_", " ")


def _compute_node_count(
    *,
    direction: CanvasElement | None,
    relevant: list[CanvasElement],
) -> int:
    total = (1 if direction is not None else 0) + len(relevant)
    if total == 1 and direction is not None and not relevant:
        return 0
    return total


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // _TOKEN_CHAR_RATIO)


def _format_insight_line(
    element: CanvasElement,
    *,
    outgoing_edges: list[CanvasConnection],
    elements_by_id: dict[UUID, CanvasElement],
) -> str:
    title = (element.title or "Untitled").strip()
    body = _excerpt(element.content_markdown)
    element_type = (element.element_type or "").strip().upper()
    line = f"- [{element_type}] {title} — {body}" if body else f"- [{element_type}] {title}"
    edge_lines: list[str] = []
    for edge in outgoing_edges:
        target = elements_by_id.get(edge.to_element_id)
        if target is None:
            continue
        target_title = (target.title or "Untitled").strip()
        label = _edge_label(edge.connection_type)
        edge_lines.append(f"  ↳ {label} → [{target_title}]")
    if edge_lines:
        return line + "\n" + "\n".join(edge_lines)
    return line


def _build_markdown(
    *,
    direction: CanvasElement | None,
    relevant: list[CanvasElement],
    connections: list[CanvasConnection],
    max_tokens: int,
) -> str:
    lines: list[str] = [
        "## Your research graph context",
        "",
    ]

    if direction is not None:
        center_title = (direction.title or "Research direction").strip()
        center_summary = (direction.content_markdown or "").strip().replace("\n", " ")
        lines.append(f"**Center:** {center_title} — {center_summary}")
        lines.append("")

    lines.append("**Relevant accepted insights:**")

    selected_ids = {el.id for el in relevant}
    if direction is not None:
        selected_ids.add(direction.id)

    elements_by_id: dict[UUID, CanvasElement] = {el.id: el for el in relevant}
    if direction is not None:
        elements_by_id[direction.id] = direction

    internal_connections = [
        c
        for c in connections
        if c.from_element_id in selected_ids and c.to_element_id in selected_ids
    ]
    outgoing_by_from: dict[UUID, list[CanvasConnection]] = {}
    for conn in internal_connections:
        outgoing_by_from.setdefault(conn.from_element_id, []).append(conn)

    def _render(current_relevant: list[CanvasElement]) -> str:
        current_insight_lines: list[str] = []
        if current_relevant:
            for element in current_relevant:
                current_insight_lines.append(
                    _format_insight_line(
                        element,
                        outgoing_edges=outgoing_by_from.get(element.id, []),
                        elements_by_id=elements_by_id,
                    )
                )
        else:
            current_insight_lines.append("- (none matched this message)")
        return "\n".join(
            lines
            + current_insight_lines
            + [
                "",
                "Use these as background when answering. Reference them when relevant "
                "and flag gaps (missing evidence, conflicting claims, open questions) "
                "when appropriate.",
            ]
        ).strip()

    trimmed = list(relevant)
    while True:
        text = _render(trimmed)
        if _estimate_tokens(text) <= max_tokens or len(trimmed) <= 1:
            return text
        trimmed = trimmed[:-1]


async def build_graph_context(
    db: AsyncSession,
    project_id: UUID,
    user_message: str,
    *,
    max_nodes: int = 10,
    max_tokens: int = 1500,
) -> GraphContextResult:
    element_repo = CanvasElementRepository(db)
    elements = await element_repo.list_non_archived_for_project(project_id=project_id)
    if not elements:
        return GraphContextResult(markdown=None, node_count=None)

    direction: CanvasElement | None = None
    non_direction: list[CanvasElement] = []
    for element in elements:
        if element.element_type == CanvasElementType.DIRECTION.value:
            if direction is None:
                direction = element
            continue
        non_direction.append(element)

    query_tokens = _tokenize_user_message(user_message)
    scored: list[tuple[int, CanvasElement]] = []
    for element in non_direction:
        score = _score_element(element, query_tokens)
        if score <= 0:
            continue
        scored.append((score, element))

    scored.sort(
        key=lambda item: (
            -item[0],
            -(item[1].updated_at.timestamp() if item[1].updated_at else 0.0),
        ),
    )

    limit = max(0, max_nodes - 1)
    relevant = [element for _, element in scored[:limit]]

    selected_ids = {el.id for el in relevant}
    if direction is not None:
        selected_ids.add(direction.id)

    connection_repo = CanvasConnectionRepository(db)
    connections = await connection_repo.list_for_project_between_elements(
        project_id=project_id,
        element_ids=selected_ids,
    )

    markdown = _build_markdown(
        direction=direction,
        relevant=relevant,
        connections=connections,
        max_tokens=max_tokens,
    )
    node_count = _compute_node_count(direction=direction, relevant=relevant)
    return GraphContextResult(markdown=markdown, node_count=node_count)
