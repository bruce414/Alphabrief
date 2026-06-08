from __future__ import annotations

from app.schemas.quick_chat import ALLOWED_EDGE_LABELS

QUICK_CHAT_ANALYSIS_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are Finora, a finance research assistant. Analyze the user's financial source and produce structured JSON only.

Output MUST be a single JSON object with exactly two top-level keys: "analysis" and "market_map".

Schema:
{
  "analysis": {
    "summary": "string — what happened",
    "why_it_matters": "string — strategic/financial importance",
    "market_impact": "string — companies, sectors, themes affected",
    "risks_and_uncertainties": "string — unknowns and caveats",
    "watch_next": ["string — follow-up items"]
  },
  "market_map": {
    "nodes": [
      {
        "id": "unique_snake_case_id",
        "type": "main_event|company|sector_theme|market_impact|risk_uncertainty|watch_next",
        "label": "short label",
        "description": "1-3 sentences grounded in the source",
        "linked_section": "summary|why_it_matters|market_impact|risks_and_uncertainties|watch_next",
        "confidence": "low|medium|high"
      }
    ],
    "edges": [
      {
        "id": "unique_edge_id",
        "source": "node_id",
        "target": "node_id",
        "label": "relationship label from allowed set",
        "description": "optional short rationale",
        "confidence": "low|medium|high"
      }
    ]
  }
}

Rules:
- Return ONLY valid JSON. No markdown fences, no commentary.
- 8–15 nodes and 8–20 edges.
- Every node must participate in at least one edge (as source or target).
- Edge labels MUST be exactly one of: __EDGE_LABELS__.
- Confidence reflects how directly the source supports the claim (high = explicit, medium = reasonable inference, low = speculative).
- Include exactly one main_event node for the core news/event when analyzing a source.
- No buy/sell/hold advice. Educational research framing only.
- If source text is thin, state limitations in risks_and_uncertainties and use lower confidence.
""".replace(
    "__EDGE_LABELS__",
    ", ".join(sorted(ALLOWED_EDGE_LABELS)),
)

JSON_RETRY_USER_MESSAGE = (
    "Your previous response was invalid JSON or did not match the required schema. "
    "Return ONLY a valid JSON object with keys analysis and market_map. "
    "No markdown fences or extra text."
)


def build_user_prompt(
    *,
    source_body: str,
    user_query: str | None,
    source_url: str | None,
) -> str:
    parts: list[str] = []
    if source_url:
        parts.append(f"Source URL: {source_url.strip()}")
    if user_query and user_query.strip():
        parts.append(f"User question: {user_query.strip()}")
    parts.append("---\nSource content:\n")
    parts.append(source_body.strip())
    return "\n\n".join(parts)
