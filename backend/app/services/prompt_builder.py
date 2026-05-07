"""Prompt assembly for segmented source analysis (PR #8b)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.core.enums import AnalysisIntent, AnalysisMode, ResearchMode, ResearchScope

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.source_segment import SourceSegment

INTENT_TO_CATEGORIES: dict[AnalysisIntent, tuple[str, ...]] = {
    AnalysisIntent.QUICK_SUMMARY: ("PERIODIC",),
    AnalysisIntent.MARKET_IMPACT: ("PERIODIC", "OWNERSHIP"),
    AnalysisIntent.COMPANY_ANALYSIS: ("PERIODIC", "GOVERNANCE", "CAPITAL_RAISE"),
    AnalysisIntent.LEARNING_MODE: ("PERIODIC", "GOVERNANCE"),
    AnalysisIntent.STRUCTURED_BRIEF: (
        "PERIODIC",
        "GOVERNANCE",
        "OWNERSHIP",
        "CAPITAL_RAISE",
    ),
    AnalysisIntent.INSIDER_ACTIVITY: ("INSIDER", "OWNERSHIP", "GOVERNANCE"),
}


def filter_enrichments_by_intent(
    enrichment_docs: list[dict], intent: AnalysisIntent
) -> list[dict]:
    allowed = INTENT_TO_CATEGORIES.get(intent, ())
    return [d for d in enrichment_docs if d.get("category") in allowed]


def build_segment_prompt(
    *,
    segment: "SourceSegment",
    analysis_intent: AnalysisIntent,
    depth: ResearchMode,
    focus_question: str | None,
    source: "Source",
    enrichment_docs: list[dict],
    research_scope: ResearchScope,
    analysis_mode: AnalysisMode,
) -> str:
    """Build the model prompt for one segment, including labeled enrichment context."""

    scope_note = (
        "Use recommended supplementary context where helpful."
        if research_scope == ResearchScope.RECOMMENDED_CONTEXT
        else "Restrict reasoning primarily to user-provided material."
    )

    mode_header = f"Analysis mode: {analysis_mode.value}"
    context_rule = ""
    if analysis_mode == AnalysisMode.CONTEXT_BRIEF:
        context_rule = (
            "\nBecause full primary-source text may be unavailable, your markdown MUST "
            'include the phrase: Full source text was not available (or clearly equivalent).\n'
        )

    enrichment_block = ""
    if enrichment_docs:
        lines = []
        for doc in enrichment_docs:
            title = doc.get("title") or doc.get("form_type") or "Document"
            summary = doc.get("summary") or doc.get("description") or ""
            cat = doc.get("category") or ""
            lines.append(f"- [{cat}] {title}: {summary}".strip())
        enrichment_block = (
            "\n## Primary-source context (SEC filings)\n"
            "Authoritative supplementary material (not the original article body):\n"
            + "\n".join(lines)
            + "\n"
        )

    entities_json = json.dumps(segment.detected_entities or [])
    topics_json = json.dumps(segment.detected_topics or [])

    fq = focus_question or "(none)"
    return (
        f"{mode_header}\n"
        f"Research scope policy: {scope_note}\n"
        f"Requested intent: {analysis_intent.value}\n"
        f"Assigned depth: {depth.value}\n"
        f"Focus question: {fq}\n"
        f"{context_rule}"
        "## Segment:\n"
        f"{segment.title or 'Untitled segment'}\n\n"
        f"SEGMENT_ENTITIES_JSON: {entities_json}\n"
        f"SEGMENT_TOPICS_JSON: {topics_json}\n"
        f"Source title: {source.title or 'Unknown'}\n"
        f"Publisher: {source.publisher or 'Unknown'}\n"
        f"{enrichment_block}\n"
        "Produce structured educational analysis in markdown. "
        "Do not give personalized investment instructions.\n"
    )
