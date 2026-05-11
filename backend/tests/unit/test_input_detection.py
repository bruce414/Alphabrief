"""Unit tests for input_detection_service.detect_input."""

from __future__ import annotations

from app.core.enums import InputType, IntentType
from app.services.input_detection_service import detect_input


def test_plain_question():
    d = detect_input("Why did Nvidia data center revenue slow?")
    assert d.urls == []
    assert d.primary_input_type == InputType.QUESTION
    assert d.intent_type == IntentType.GENERAL_ASK


def test_single_article_url():
    d = detect_input("Here is coverage https://www.reuters.com/markets/foo.html")
    assert len(d.urls) == 1
    assert d.per_url_type == [InputType.ARTICLE_URL]
    assert d.primary_input_type == InputType.ARTICLE_URL
    assert d.intent_type == IntentType.SOURCE_ANALYSIS


def test_single_youtube_url():
    d = detect_input("https://www.youtube.com/watch?v=dQw4w9WgXcQ explain this")
    assert d.urls == ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    assert d.per_url_type == [InputType.YOUTUBE_URL]
    assert d.primary_input_type == InputType.YOUTUBE_URL
    assert d.intent_type == IntentType.SOURCE_ANALYSIS


def test_sec_edgar_url():
    d = detect_input("10-K https://www.sec.gov/Archives/edgar/data/123/x.htm")
    assert len(d.urls) == 1
    assert d.per_url_type == [InputType.FILING_URL]
    assert d.primary_input_type == InputType.FILING_URL
    assert d.intent_type == IntentType.SOURCE_ANALYSIS


def test_mixed_urls():
    d = detect_input(
        "Compare https://www.reuters.com/a and https://www.youtube.com/watch?v=abc"
    )
    assert len(d.urls) == 2
    assert d.per_url_type == [InputType.ARTICLE_URL, InputType.YOUTUBE_URL]
    assert d.primary_input_type == InputType.MIXED
    assert d.intent_type == IntentType.SOURCE_ANALYSIS


def test_generate_a_brief_from_this():
    d = detect_input("generate a brief from this")
    assert d.primary_input_type == InputType.QUESTION
    assert d.intent_type == IntentType.BRIEF_GENERATION
