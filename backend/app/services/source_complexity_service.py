"""Complexity scoring + per-run impact estimation for the cheap pre-scan.

See AI_PIPELINE.md §17.1 / §17.4 and DATA_MODEL.md §4.15. This module is
deliberately pure (no DB, no I/O) so it stays cheap and easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings


# Multiplier on per-segment estimated tokens per requested research depth.
# Quick = single-pass summary, Standard = ~2x analysis, Deep = ~4x with
# cross-checks. Tune against real telemetry before raising further.
DEPTH_TOKEN_MULTIPLIER: dict[str, float] = {
    "QUICK": 1.0,
    "STANDARD": 2.0,
    "DEEP": 4.0,
}


@dataclass(frozen=True)
class SegmentEstimate:
    """Minimum interface a segment exposes to the impact estimator."""

    estimated_tokens: int
    has_text: bool


def score_complexity(
    word_count: int,
    entity_count: int,
    topic_count: int,
) -> str:
    """Return one of LOW / MEDIUM / HIGH / VERY_HIGH (DATA_MODEL §4.15)."""

    raw = (
        0.5 * min(max(word_count, 0) / 10_000, 1.0)
        + 0.3 * min(max(entity_count, 0) / 30, 1.0)
        + 0.2 * min(max(topic_count, 0) / 15, 1.0)
    )
    if raw < 0.25:
        return "LOW"
    if raw < 0.5:
        return "MEDIUM"
    if raw < 0.75:
        return "HIGH"
    return "VERY_HIGH"


def warning_level_for(percent: float) -> tuple[str, bool]:
    """Map an impact percent onto the (warning_level, requires_warning) ladder.

    AI_PIPELINE §17.4:
        pct < 30   → NONE
        30 <= pct < 50 → INLINE
        50 <= pct < 80 → HIGH (requires warning)
        pct >= 80      → VERY_HIGH (requires warning)
    """

    if percent < 30:
        return "NONE", False
    if percent < 50:
        return "INLINE", False
    if percent < 80:
        return "HIGH", True
    return "VERY_HIGH", True


def estimate_impact_percent(
    segments: list[SegmentEstimate],
    requested_mode: str,
    single_run_token_budget: int | None = None,
) -> tuple[float, str]:
    """Estimate (allowance_impact_percent, estimate_confidence).

    Confidence is HIGH when every segment exposed real text/transcript content;
    LOW when the only segment we have is metadata-only synthetic; otherwise
    MEDIUM (mixed). UNKNOWN is reserved for the no-segments edge case.
    """

    if requested_mode not in DEPTH_TOKEN_MULTIPLIER:
        raise ValueError(f"Unsupported research mode: {requested_mode!r}")

    budget = (
        single_run_token_budget
        if single_run_token_budget is not None
        else get_settings().single_run_token_budget
    )
    if budget <= 0:
        raise ValueError("single_run_token_budget must be positive")

    if not segments:
        return 0.0, "UNKNOWN"

    multiplier = DEPTH_TOKEN_MULTIPLIER[requested_mode]
    total_tokens = sum(seg.estimated_tokens for seg in segments) * multiplier
    pct = (total_tokens / budget) * 100
    pct = max(0.0, min(pct, 100.0))

    has_text_count = sum(1 for s in segments if s.has_text)
    if has_text_count == len(segments):
        confidence = "HIGH"
    elif has_text_count == 0:
        confidence = "LOW"
    else:
        confidence = "MEDIUM"

    return pct, confidence


def recommend_research_mode(
    complexity: str,
    requested_mode: str,
    warning_level: str,
) -> str:
    """Pick a recommended research mode given complexity + warning level.

    Conservative defaults: never push the user up, only suggest stepping down
    when the impact estimate trips the strong warning threshold.
    """

    if warning_level == "VERY_HIGH":
        return "QUICK" if complexity == "VERY_HIGH" else "STANDARD"
    if warning_level == "HIGH":
        if requested_mode == "DEEP":
            return "STANDARD"
        return requested_mode
    return requested_mode


def recommend_completion_strategy(warning_level: str, complexity: str) -> str:
    """Pick STRICT_REQUESTED_MODE vs OPTIMIZE_RESEARCH (AI_PIPELINE §17.5)."""

    if warning_level in ("HIGH", "VERY_HIGH"):
        return "OPTIMIZE_RESEARCH"
    if complexity in ("HIGH", "VERY_HIGH"):
        return "OPTIMIZE_RESEARCH"
    return "STRICT_REQUESTED_MODE"


def estimate_segment_tokens(word_count: int) -> int:
    """Conservative word-to-token estimate. ~1.33 tokens per English word."""

    return max(1, int(round(max(word_count, 0) * 1.33)))
