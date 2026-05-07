"""Validate segment-level AI output before persistence (PR #8b)."""

from __future__ import annotations

import bleach

from app.clients.ai_provider_client import SegmentAnalysisResult
from app.core.enums import AnalysisMode

_ALLOWED_TAGS = frozenset(
    {
        "p",
        "br",
        "strong",
        "em",
        "b",
        "i",
        "u",
        "ul",
        "ol",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "code",
        "pre",
        "blockquote",
        "span",
        "a",
    }
)

_VALID_CONFIDENCE = frozenset({"HIGH", "MEDIUM", "LOW", "UNKNOWN"})

_CONTEXT_BRIEF_PHRASES = (
    "full source text was not available",
    "full text was not available",
    "full primary text was not available",
)

_ADVICE_PHRASES = (
    "buy this stock",
    "guaranteed return",
    "you should invest",
)


def sanitize_analysis_markdown(text: str) -> str:
    return bleach.clean(text, tags=_ALLOWED_TAGS, strip=True)


def validate_segment_output(
    result: SegmentAnalysisResult,
    *,
    analysis_mode: AnalysisMode,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    if not (result.analysis_markdown or "").strip():
        errors.append("analysis_markdown is empty")

    if result.key_entities is None:
        errors.append("key_entities is missing")

    if result.key_topics is None:
        errors.append("key_topics is missing")

    label = (result.confidence_label or "").strip().upper()
    if label not in _VALID_CONFIDENCE:
        errors.append("confidence_label must be one of HIGH, MEDIUM, LOW, UNKNOWN")

    md_lower = (result.analysis_markdown or "").lower()
    if "<script" in md_lower:
        errors.append("analysis_markdown contains forbidden script markup")

    sanitized = sanitize_analysis_markdown(result.analysis_markdown or "")
    if sanitized != (result.analysis_markdown or "") and "<script" in (
        result.analysis_markdown or ""
    ).lower():
        errors.append("analysis_markdown failed sanitization")

    if analysis_mode == AnalysisMode.CONTEXT_BRIEF:
        if not any(p in md_lower for p in _CONTEXT_BRIEF_PHRASES):
            errors.append("CONTEXT_BRIEF output must disclose unavailable full text")

    for phrase in _ADVICE_PHRASES:
        if phrase in md_lower:
            errors.append(f"disallowed phrase: {phrase!r}")

    return (len(errors) == 0, errors)


def repair_suffix(errors: list[str]) -> str:
    return (
        "\n\n---\nYour previous answer failed validation:\n- "
        + "\n- ".join(errors)
        + "\nProvide a corrected answer that satisfies every rule above."
    )
