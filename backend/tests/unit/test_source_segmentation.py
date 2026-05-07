"""Unit tests for source segmentation (no DB / no API)."""

from __future__ import annotations

from app.services.source_segmentation_service import (
    TranscriptCaption,
    captions_from_text_estimate,
    segment_article,
    segment_metadata_only,
    segment_youtube_transcript,
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
