"""Pure segmentation helpers for the cheap pre-scan (AI_PIPELINE §17.2).

These functions return in-memory `SegmentDraft` records. Persistence + entity
detection live in `source_scan_service`. Keeping segmentation pure makes it
easy to feed fixtures (article HTML, transcript captions) directly in tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# Roughly how many words fit in a 400-word paragraph window for ARTICLE_URL.
ARTICLE_TARGET_WORDS = 400
# YouTube grouping window. Picking 4 minutes (240s) lands inside the 3-5 minute
# guidance from the prompt and keeps segment counts comfortable for a 30 minute
# video (~7-8 segments).
YOUTUBE_TARGET_WINDOW_SECONDS = 240
# A segment that ends up longer than this is ugly; flush early when crossed.
YOUTUBE_MAX_WINDOW_SECONDS = 300

# Segment titles get a 60-char placeholder per the prompt; the first LLM pass
# in a later PR will rewrite this with a real heading.
TITLE_PLACEHOLDER_CHARS = 60


@dataclass
class SegmentDraft:
    """In-memory segment built by the segmentation pass.

    Persistence-time fields like ``id`` and ``source_scan_id`` are filled by
    the orchestrating service; this record stays decoupled from SQLAlchemy.
    """

    segment_index: int
    text: str
    word_count: int
    start_offset_seconds: int | None = None
    end_offset_seconds: int | None = None
    start_char_offset: int | None = None
    end_char_offset: int | None = None
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    has_text: bool = True


@dataclass(frozen=True)
class TranscriptCaption:
    """One caption row from a timed transcript (text, start, duration)."""

    text: str
    start: float
    duration: float


_HEADING_LINE_RE = re.compile(r"^(#{2,3})\s+(.+)$")


def _word_count(text: str) -> int:
    return len(text.split()) if text else 0


def _short_title(text: str) -> str:
    snippet = text.strip().replace("\n", " ")
    snippet = re.sub(r"\s+", " ", snippet)
    if len(snippet) <= TITLE_PLACEHOLDER_CHARS:
        return snippet
    return snippet[:TITLE_PLACEHOLDER_CHARS].rstrip() + "…"


def segment_article(extracted_text: str) -> list[SegmentDraft]:
    """Segment article text. Splits on markdown-style h2/h3 if present, else
    groups paragraphs into ~ARTICLE_TARGET_WORDS windows."""

    if not extracted_text or not extracted_text.strip():
        return []

    headings = _split_on_markdown_headings(extracted_text)
    if headings is not None and len(headings) >= 2:
        return [
            SegmentDraft(
                segment_index=i,
                text=block.text,
                word_count=_word_count(block.text),
                start_char_offset=block.start,
                end_char_offset=block.end,
                title=block.title or _short_title(block.text),
                has_text=True,
            )
            for i, block in enumerate(headings)
        ]

    return _paragraph_windows(extracted_text)


def segment_youtube_transcript(
    captions: list[TranscriptCaption],
    *,
    target_window_seconds: int = YOUTUBE_TARGET_WINDOW_SECONDS,
    max_window_seconds: int = YOUTUBE_MAX_WINDOW_SECONDS,
) -> list[SegmentDraft]:
    """Group caption rows into ~3-5 minute windows."""

    if not captions:
        return []

    drafts: list[SegmentDraft] = []
    bucket: list[TranscriptCaption] = []
    bucket_start: float | None = None

    def _flush() -> None:
        if not bucket:
            return
        text = " ".join(c.text.strip() for c in bucket if c.text and c.text.strip()).strip()
        if not text:
            bucket.clear()
            return
        start_s = int(round(bucket_start or 0))
        end_s = int(round(bucket[-1].start + bucket[-1].duration))
        drafts.append(
            SegmentDraft(
                segment_index=len(drafts),
                text=text,
                word_count=_word_count(text),
                start_offset_seconds=start_s,
                end_offset_seconds=end_s,
                title=_short_title(text),
                has_text=True,
            )
        )
        bucket.clear()

    for cap in captions:
        if bucket_start is None:
            bucket_start = cap.start
        bucket.append(cap)
        elapsed = (cap.start + cap.duration) - bucket_start
        if elapsed >= target_window_seconds:
            _flush()
            bucket_start = None
        elif elapsed >= max_window_seconds:
            _flush()
            bucket_start = None

    _flush()
    return drafts


def captions_from_text_estimate(
    text: str,
    *,
    words_per_minute: float = 150.0,
) -> list[TranscriptCaption]:
    """Fallback when only joined transcript text is available.

    Splits into ~10 second pseudo-captions assuming an average speaking rate of
    150 wpm (≈ 25 words / caption). Used when timed captions can't be re-fetched
    at scan time but a transcript blob exists.
    """

    if not text or not text.strip():
        return []
    words = text.split()
    words_per_caption = max(1, int(round((words_per_minute / 60.0) * 10)))
    captions: list[TranscriptCaption] = []
    t = 0.0
    duration = 10.0
    for i in range(0, len(words), words_per_caption):
        chunk = " ".join(words[i : i + words_per_caption])
        captions.append(TranscriptCaption(text=chunk, start=t, duration=duration))
        t += duration
    return captions


def segment_metadata_only(*, title: str | None, text_hint: str | None = None) -> list[SegmentDraft]:
    """Synthetic single segment for METADATA_ONLY sources."""

    body = (title or text_hint or "Source metadata only").strip()
    return [
        SegmentDraft(
            segment_index=0,
            text=body,
            word_count=_word_count(body),
            title=_short_title(body),
            metadata={"metadataOnly": True},
            has_text=False,
        )
    ]


@dataclass(frozen=True)
class _HeadingBlock:
    title: str
    text: str
    start: int
    end: int


def _split_on_markdown_headings(text: str) -> list[_HeadingBlock] | None:
    """Return heading-delimited blocks if the text contains h2/h3 markers."""

    if "##" not in text:
        return None

    lines = text.splitlines(keepends=True)
    blocks: list[_HeadingBlock] = []
    cursor = 0
    current_title: str | None = None
    current_buf: list[str] = []
    current_start = 0

    def _flush(end_offset: int) -> None:
        if not current_buf:
            return
        body = "".join(current_buf).strip()
        if not body:
            return
        blocks.append(
            _HeadingBlock(
                title=current_title or _short_title(body),
                text=body,
                start=current_start,
                end=end_offset,
            )
        )

    for line in lines:
        m = _HEADING_LINE_RE.match(line.strip())
        if m is not None:
            _flush(cursor)
            current_title = m.group(2).strip()
            current_buf = []
            current_start = cursor + len(line)
        else:
            current_buf.append(line)
        cursor += len(line)

    _flush(cursor)
    if len(blocks) < 2:
        return None
    return blocks


def _paragraph_windows(text: str) -> list[SegmentDraft]:
    """Group paragraphs into ~ARTICLE_TARGET_WORDS chunks, preserving offsets."""

    drafts: list[SegmentDraft] = []
    paragraphs = _iter_paragraphs(text)

    buf_paragraphs: list[tuple[str, int, int]] = []
    buf_words = 0
    buf_start: int | None = None

    def _flush() -> None:
        nonlocal buf_paragraphs, buf_words, buf_start
        if not buf_paragraphs:
            return
        body = "\n\n".join(p for p, _, _ in buf_paragraphs).strip()
        if not body:
            buf_paragraphs = []
            buf_words = 0
            buf_start = None
            return
        start = buf_paragraphs[0][1] if buf_start is None else buf_start
        end = buf_paragraphs[-1][2]
        drafts.append(
            SegmentDraft(
                segment_index=len(drafts),
                text=body,
                word_count=_word_count(body),
                start_char_offset=start,
                end_char_offset=end,
                title=_short_title(body),
                has_text=True,
            )
        )
        buf_paragraphs = []
        buf_words = 0
        buf_start = None

    for para, start, end in paragraphs:
        para_words = _word_count(para)
        if buf_start is None:
            buf_start = start
        buf_paragraphs.append((para, start, end))
        buf_words += para_words
        if buf_words >= ARTICLE_TARGET_WORDS:
            _flush()

    _flush()

    if not drafts:
        # Single short paragraph fallback - keep at least one segment.
        body = text.strip()
        drafts.append(
            SegmentDraft(
                segment_index=0,
                text=body,
                word_count=_word_count(body),
                start_char_offset=0,
                end_char_offset=len(text),
                title=_short_title(body),
                has_text=True,
            )
        )
    return drafts


def _iter_paragraphs(text: str) -> list[tuple[str, int, int]]:
    """Split text into (paragraph, start_char, end_char) tuples on blank lines.

    Falls back to single-line paragraphs when the text contains no blank lines
    so we still produce some windows for tightly formatted extractions.
    """

    out: list[tuple[str, int, int]] = []
    if "\n\n" in text:
        cursor = 0
        for chunk in re.split(r"(\n\s*\n)", text):
            if chunk and chunk.strip() and not chunk.startswith("\n"):
                start = cursor
                end = cursor + len(chunk)
                out.append((chunk.strip(), start, end))
            cursor += len(chunk)
        if out:
            return out

    cursor = 0
    for line in text.splitlines(keepends=True):
        if line.strip():
            start = cursor
            end = cursor + len(line)
            out.append((line.strip(), start, end))
        cursor += len(line)
    return out
