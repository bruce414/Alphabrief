"""Unit tests for the cheap entity / topic detector."""

from __future__ import annotations

from app.services.entity_detection_service import (
    detect_companies,
    detect_entities,
    detect_tickers,
    detect_topics,
)


SAMPLE = (
    "Nvidia continues to dominate AI chips while Visa reported strong earnings. "
    "Analysts compare NVDA versus AMD margin trends. The Fed remains cautious as "
    "tariffs and oil prices weigh on consumer spending. AAPL guidance was solid."
)


def test_detect_tickers_picks_up_allowlisted_only():
    tickers = detect_tickers(SAMPLE)
    assert "NVDA" in tickers
    assert "AMD" in tickers
    assert "AAPL" in tickers
    # Random uppercase noise that isn't an allowlisted ticker should not appear.
    assert "ZZZZ" not in tickers


def test_detect_companies_normalizes_names_and_attaches_tickers():
    companies = detect_companies(SAMPLE)
    by_name = {name: ticker for name, ticker in companies}
    assert by_name.get("Nvidia") == "NVDA"
    assert by_name.get("Visa") == "V"


def test_detect_entities_dedups_company_and_bare_ticker():
    entities = detect_entities(SAMPLE)
    nvda = [e for e in entities if e.ticker == "NVDA"]
    # Only one NVDA entry expected (company), not also a TICKER row.
    assert len(nvda) == 1
    assert nvda[0].type == "COMPANY"
    assert any(e.name == "Visa" and e.type == "COMPANY" for e in entities)
    # AAPL appears bare in the sample with no "Apple" string nearby, so it
    # should surface as a plain TICKER, not a COMPANY entry.
    assert any(e.name == "AAPL" and e.type == "TICKER" for e in entities)


def test_detect_topics_matches_macro_keywords():
    topics = detect_topics(SAMPLE)
    assert "AI chips" in topics
    assert "earnings" in topics
    assert "Fed" in topics
    assert "tariffs" in topics
    assert "oil" in topics


def test_empty_text_returns_empty_lists():
    assert detect_tickers("") == []
    assert detect_companies("") == []
    assert detect_topics("") == []
    assert detect_entities("") == []
