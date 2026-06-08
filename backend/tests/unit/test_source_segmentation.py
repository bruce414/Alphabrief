"""Unit tests for source segmentation (no DB / no API)."""

from __future__ import annotations

from app.services.source_segmentation_service import (
    TranscriptCaption,
    captions_from_text_estimate,
    segment_article,
    segment_metadata_only,
    segment_youtube_transcript,
    url_slug_to_text,
)


def _build_article_text(num_paragraphs: int, words_per_paragraph: int) -> str:
    """Generate a deterministic plain-text article without markdown headings."""

    paragraphs: list[str] = []
    for p in range(num_paragraphs):
        words = [f"alpha{p:03d}word{w:03d}" for w in range(words_per_paragraph)]
        paragraphs.append(" ".join(words))
    return "\n\n".join(paragraphs)


def test_segment_article_2000_words_yields_at_least_5_segments():
    text = _build_article_text(num_paragraphs=20, words_per_paragraph=100)
    drafts = segment_article(text)
    assert len(drafts) >= 5
    assert sum(d.word_count for d in drafts) >= 2000
    assert all(d.has_text for d in drafts)
    for i, d in enumerate(drafts):
        assert d.segment_index == i
        assert d.start_char_offset is not None
        assert d.end_char_offset is not None


def test_segment_article_with_markdown_headings_splits_on_them():
    text = (
        "## Intro\n"
        "Setup paragraph with several words and a short market overview.\n\n"
        "## Earnings recap\n"
        "Body discussing earnings, guidance and margin commentary.\n\n"
        "### Risks\n"
        "Concluding paragraph about credit, geopolitics, and supply chain.\n"
    )
    drafts = segment_article(text)
    assert len(drafts) >= 3
    titles = [d.title for d in drafts]
    assert any("Intro" in (t or "") for t in titles)
    assert any("Earnings recap" in (t or "") for t in titles)


def test_segment_article_short_text_still_yields_one_segment():
    text = "Short standalone paragraph."
    drafts = segment_article(text)
    assert len(drafts) == 1
    assert drafts[0].segment_index == 0
    assert drafts[0].word_count == 3


def test_segment_youtube_transcript_30_minutes_yields_6_to_10_segments():
    captions: list[TranscriptCaption] = []
    duration = 5.0  # 5-second caption rows
    total_seconds = 30 * 60
    t = 0.0
    while t < total_seconds:
        captions.append(TranscriptCaption(text=f"line at {int(t)}s", start=t, duration=duration))
        t += duration
    drafts = segment_youtube_transcript(captions)
    assert 6 <= len(drafts) <= 10
    assert drafts[0].start_offset_seconds == 0
    assert drafts[-1].end_offset_seconds is not None
    assert drafts[-1].end_offset_seconds >= total_seconds - 10


def test_captions_from_text_estimate_30_minutes_yields_6_to_10_segments():
    # 30 minutes at 150 wpm ≈ 4500 words
    text = " ".join(["word"] * 4500)
    captions = captions_from_text_estimate(text)
    drafts = segment_youtube_transcript(captions)
    assert 6 <= len(drafts) <= 10


def test_segment_metadata_only_returns_single_synthetic_segment():
    drafts = segment_metadata_only(title="Some article title", text_hint=None)
    assert len(drafts) == 1
    assert drafts[0].segment_index == 0
    assert drafts[0].has_text is False
    assert drafts[0].metadata.get("metadataOnly") is True


def test_segment_metadata_only_harvests_url_slug_when_title_is_empty():
    """A barrons-style paywall URL should still surface the slug keywords."""

    drafts = segment_metadata_only(
        title=None,
        url="https://www.barrons.com/articles/apple-stock-record-track-june-5a777ea2",
    )
    assert len(drafts) == 1
    body = drafts[0].text.lower()
    assert "apple" in body
    assert "stock" in body
    # Hex-like article ids should be dropped.
    assert "5a777ea2" not in body
    assert drafts[0].metadata.get("slugTextUsed") is True


def test_segment_metadata_only_concatenates_title_description_and_slug():
    drafts = segment_metadata_only(
        title="Apple stock on track for June record",
        description="Bullish setup for AAPL into earnings.",
        publisher="Barron's",
        url="https://www.barrons.com/articles/apple-stock-record-track-june-5a777ea2",
    )
    assert len(drafts) == 1
    body = drafts[0].text
    assert "Apple stock on track for June record" in body
    assert "AAPL" in body
    assert "Barron's" in body
    assert "apple stock record track june" in body.lower()


def test_segment_metadata_only_handles_no_signals_at_all():
    drafts = segment_metadata_only(title=None, url=None)
    assert len(drafts) == 1
    assert drafts[0].text == "Source metadata only"
    assert drafts[0].metadata.get("slugTextUsed") is False


def test_url_slug_to_text_drops_short_path_prefixes_and_hashes():
    assert url_slug_to_text(
        "https://www.barrons.com/articles/apple-stock-record-track-june-5a777ea2"
    ) == "apple stock record track june"
    assert url_slug_to_text(
        "https://www.example.com/news/2025/10/nvidia-earnings-preview-1234"
    ).startswith("nvidia earnings preview")


def test_url_slug_to_text_returns_empty_for_uninformative_paths():
    assert url_slug_to_text("https://example.com") == ""
    assert url_slug_to_text("https://example.com/") == ""
    assert url_slug_to_text(None) == ""
