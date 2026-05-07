"""Unit tests for complexity scoring and per-run impact estimation."""

from __future__ import annotations

import pytest

from app.services.source_complexity_service import (
    DEPTH_TOKEN_MULTIPLIER,
    SegmentEstimate,
    estimate_impact_percent,
    recommend_completion_strategy,
    recommend_research_mode,
    score_complexity,
    warning_level_for,
)


def test_score_complexity_low_for_short_low_density():
    assert score_complexity(word_count=500, entity_count=2, topic_count=1) == "LOW"


def test_score_complexity_medium_for_mid_signals():
    assert score_complexity(word_count=4_000, entity_count=10, topic_count=4) == "MEDIUM"


def test_score_complexity_high_for_dense_content():
    # raw = 0.5*0.8 + 0.3*0.66... + 0.2*0.66... = 0.4 + 0.2 + 0.133 = 0.733 → HIGH
    assert score_complexity(word_count=8_000, entity_count=20, topic_count=10) == "HIGH"


def test_score_complexity_very_high_at_saturation():
    assert score_complexity(word_count=20_000, entity_count=60, topic_count=30) == "VERY_HIGH"


def test_estimate_impact_scales_4x_between_quick_and_deep():
    segments = [SegmentEstimate(estimated_tokens=10_000, has_text=True) for _ in range(3)]
    quick_pct, _ = estimate_impact_percent(
        segments, "QUICK", single_run_token_budget=1_000_000
    )
    deep_pct, _ = estimate_impact_percent(
        segments, "DEEP", single_run_token_budget=1_000_000
    )
    assert deep_pct == pytest.approx(quick_pct * 4)
    assert DEPTH_TOKEN_MULTIPLIER["DEEP"] / DEPTH_TOKEN_MULTIPLIER["QUICK"] == 4.0


def test_estimate_impact_clamped_at_100_percent():
    huge = [SegmentEstimate(estimated_tokens=10_000_000, has_text=True)]
    pct, _ = estimate_impact_percent(huge, "DEEP", single_run_token_budget=200_000)
    assert pct == 100.0


def test_estimate_impact_confidence_high_when_all_segments_have_text():
    segments = [SegmentEstimate(estimated_tokens=1_000, has_text=True) for _ in range(2)]
    _, confidence = estimate_impact_percent(
        segments, "STANDARD", single_run_token_budget=1_000_000
    )
    assert confidence == "HIGH"


def test_estimate_impact_confidence_low_when_metadata_only():
    segments = [SegmentEstimate(estimated_tokens=10, has_text=False)]
    _, confidence = estimate_impact_percent(
        segments, "STANDARD", single_run_token_budget=1_000_000
    )
    assert confidence == "LOW"


def test_estimate_impact_unknown_when_no_segments():
    pct, confidence = estimate_impact_percent(
        [], "QUICK", single_run_token_budget=200_000
    )
    assert pct == 0.0
    assert confidence == "UNKNOWN"


def test_estimate_impact_rejects_unknown_research_mode():
    with pytest.raises(ValueError):
        estimate_impact_percent(
            [SegmentEstimate(estimated_tokens=1, has_text=True)],
            "BANANA",
            single_run_token_budget=1_000,
        )


@pytest.mark.parametrize(
    "percent,expected_level,expected_warn",
    [
        (25.0, "NONE", False),
        (40.0, "INLINE", False),
        (60.0, "HIGH", True),
        (85.0, "VERY_HIGH", True),
    ],
)
def test_warning_level_threshold_ladder(percent, expected_level, expected_warn):
    level, requires = warning_level_for(percent)
    assert level == expected_level
    assert requires is expected_warn


def test_recommend_research_mode_steps_down_on_strong_warning():
    assert recommend_research_mode("HIGH", "DEEP", "HIGH") == "STANDARD"
    assert recommend_research_mode("VERY_HIGH", "DEEP", "VERY_HIGH") == "QUICK"


def test_recommend_research_mode_passthrough_when_no_warning():
    assert recommend_research_mode("LOW", "DEEP", "NONE") == "DEEP"


def test_recommend_completion_strategy_optimizes_when_warned():
    assert recommend_completion_strategy("HIGH", "MEDIUM") == "OPTIMIZE_RESEARCH"
    assert recommend_completion_strategy("NONE", "VERY_HIGH") == "OPTIMIZE_RESEARCH"
    assert recommend_completion_strategy("NONE", "LOW") == "STRICT_REQUESTED_MODE"
