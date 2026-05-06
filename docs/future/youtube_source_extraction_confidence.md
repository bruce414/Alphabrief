# YouTube Source Extraction Confidence Logic for AlphaBrief

## Summary

The current Cursor implementation uses this simple rule:

```text
HIGH confidence if:
1. YouTube transcript is available
2. transcript word count > 200
```

This is a decent first-pass heuristic, but it is not strong enough for a product-quality AlphaBrief source extraction confidence system.

It is acceptable for a v0.3 prototype, but it should be improved before users rely on the analysis quality.

---

## Current Logic

```text
HIGH confidence if:
1. YouTube transcript is available
2. transcript word count > 200
```

This is reasonable because:

- transcript availability means AlphaBrief has real source text to analyze
- `> 200 words` filters out very short clips, empty transcripts, Shorts, trailers, or broken fetches
- it is simple and easy to test

For the **v0.3 first milestone**, this is acceptable as a basic guardrail.

However, it is not enough if the goal is user trust and reliable analysis quality.

---

## Why the Current Logic Is Not Strong Enough

### 1. Transcript availability does not mean transcript quality

A transcript can exist but still be bad:

```text
[Music]
thank you
foreign
uh yeah so anyway
```

or:

```text
welcome back guys smash the like button today we are going to...
```

Technically, the transcript is available. Analytically, it may be almost useless.

So availability alone should not equal high confidence.

---

### 2. Word count alone is too shallow

`200+ words` only tells you the transcript has some length.

It does **not** tell you:

- whether the transcript is meaningful
- whether it is in a supported language
- whether it is mostly filler
- whether it contains finance, market, or company content
- whether it matches the user's requested analysis mode
- whether it covers the actual topic of the video
- whether it is auto-generated and messy

A transcript can be long but still low-value.

---

### 3. Auto-generated transcripts should slightly reduce confidence

Auto-generated transcripts are often usable, so they should not automatically be rejected.

But they should be treated with slightly less confidence than manually provided captions.

Example:

```text
Manual English transcript, 1,500 words -> stronger
Auto-generated English transcript, 1,500 words -> still usable, but slightly less trusted
Auto-generated transcript with broken tokens -> weaker
```

---

## Better Confidence Logic

Instead of a binary rule, use a score or category-based confidence system.

Recommended categories:

```text
0.80 - 1.00 = high
0.50 - 0.79 = medium
0.20 - 0.49 = low
0.00 - 0.19 = unusable
```

For v0.3, a simple category-based rule is probably enough.

---

## Recommended v0.3 Signals

| Signal | Why it matters |
|---|---|
| Transcript available | Required for transcript-based analysis |
| Word count | Checks whether enough source material exists |
| Language | Ensures the transcript is in a supported language |
| Is auto-generated | Manual captions are usually more reliable |
| Meaningful text ratio | Filters `[Music]`, filler, broken transcript text |
| Finance relevance | Checks whether the video is relevant to AlphaBrief |
| Source metadata available | Title, channel, date, and description can help fallback/context |

---

## Suggested Confidence Levels

### High Confidence

Use `HIGH` when:

```text
transcript_available = true
word_count >= 500
meaningful_text_ratio >= 0.75
language_code is supported
finance_relevance_score >= 0.5
```

Optional boost:

```text
manual transcript OR clean auto-generated transcript
```

This means AlphaBrief has enough source material to produce a proper brief.

---

### Medium Confidence

Use `MEDIUM` when:

```text
transcript_available = true
word_count between 200 and 499
meaningful_text_ratio >= 0.6
language_code is supported
```

or:

```text
transcript_available = true
word_count >= 500
but finance relevance is unclear
```

This is usable, but the final output should mention that the analysis is based on a limited or partially relevant transcript.

Example user-facing message:

```text
Analysis is based on a limited or partially relevant transcript.
```

---

### Low Confidence

Use `LOW` when:

```text
transcript_available = true
word_count < 200
```

or:

```text
meaningful_text_ratio is low
```

or:

```text
transcript is mostly [Music], repeated phrases, intros, sponsor reads, or fragmented captions
```

This should not automatically trigger deep analysis.

---

### Unavailable / Failed

Separate these clearly:

```text
NO_TRANSCRIPT
VIDEO_UNAVAILABLE
NETWORK_BLOCKED
FETCH_FAILED
UNSUPPORTED_LANGUAGE
```

Do **not** merge all of these into `LOW`, because that creates confusing backend and UX behavior.

---

## Recommended Data Model Shape

```python
from enum import Enum
from dataclasses import dataclass


class SourceExtractionConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNUSABLE = "unusable"
    UNKNOWN = "unknown"


@dataclass
class YouTubeTranscriptQuality:
    transcript_available: bool
    word_count: int
    language_code: str | None
    is_generated: bool | None
    meaningful_text_ratio: float
    finance_relevance_score: float | None
    confidence: SourceExtractionConfidence
    reasons: list[str]
```

---

## Recommended Confidence Classification Function

```python
from enum import Enum


class SourceExtractionConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNUSABLE = "unusable"
    UNKNOWN = "unknown"


def classify_youtube_transcript_confidence(
    transcript_available: bool,
    word_count: int,
    language_code: str | None,
    is_generated: bool | None,
    meaningful_text_ratio: float,
    finance_relevance_score: float | None,
) -> tuple[SourceExtractionConfidence, list[str]]:
    reasons = []

    if not transcript_available:
        return SourceExtractionConfidence.UNUSABLE, [
            "No accessible transcript is available."
        ]

    if language_code not in {"en", "zh", "zh-Hans", "zh-Hant"}:
        return SourceExtractionConfidence.LOW, [
            f"Transcript language '{language_code}' is not currently well supported."
        ]

    if word_count < 100:
        return SourceExtractionConfidence.UNUSABLE, [
            "Transcript is too short for reliable analysis."
        ]

    if word_count < 200:
        reasons.append("Transcript is short.")
        return SourceExtractionConfidence.LOW, reasons

    if meaningful_text_ratio < 0.5:
        return SourceExtractionConfidence.LOW, [
            "Transcript appears to contain too much non-substantive text."
        ]

    if word_count >= 500 and meaningful_text_ratio >= 0.75:
        if finance_relevance_score is not None and finance_relevance_score < 0.4:
            return SourceExtractionConfidence.MEDIUM, [
                "Transcript is readable, but finance relevance is unclear."
            ]

        reasons.append("Transcript has enough readable source material.")

        if is_generated:
            reasons.append("Transcript is auto-generated, so minor errors may exist.")
        else:
            reasons.append("Transcript appears to be manually provided.")

        return SourceExtractionConfidence.HIGH, reasons

    return SourceExtractionConfidence.MEDIUM, [
        "Transcript is available but has limited length or quality signals."
    ]
```

---

## Simple Meaningful Text Ratio

This can be calculated without an LLM first.

```python
import re


NON_MEANINGFUL_PATTERNS = [
    r"\[music\]",
    r"\[applause\]",
    r"\[laughter\]",
    r"\(music\)",
    r"thank you",
    r"foreign",
]


def calculate_meaningful_text_ratio(text: str) -> float:
    words = re.findall(r"\b\w+\b", text.lower())

    if not words:
        return 0.0

    non_meaningful_count = 0

    for word in words:
        if len(word) <= 1:
            non_meaningful_count += 1

    lowered = text.lower()

    for pattern in NON_MEANINGFUL_PATTERNS:
        matches = re.findall(pattern, lowered)
        non_meaningful_count += len(matches) * 2

    meaningful_count = max(len(words) - non_meaningful_count, 0)

    return meaningful_count / len(words)
```

This is crude, but good enough for v0.3. Later, it can be replaced with a lightweight LLM pre-scan.

---

## Simple Finance Relevance Score

For v0.3, use keyword-based scoring before spending LLM tokens.

```python
FINANCE_KEYWORDS = {
    "stock", "stocks", "market", "markets", "investor", "investors",
    "revenue", "earnings", "profit", "margin", "valuation", "growth",
    "inflation", "rates", "interest", "fed", "tariff", "macro",
    "shares", "equity", "cash flow", "balance sheet", "income statement",
    "guidance", "forecast", "analyst", "sector", "industry",
}


def calculate_finance_relevance_score(text: str) -> float:
    lowered = text.lower()
    matched = 0

    for keyword in FINANCE_KEYWORDS:
        if keyword in lowered:
            matched += 1

    return min(matched / 10, 1.0)
```

Suggested interpretation:

```text
0.0 - 0.2 = probably not finance-related
0.3 - 0.5 = maybe relevant
0.6+ = likely relevant
```

---

## Recommended Replacement for Cursor's Current Logic

Change this:

```text
HIGH = transcript_available AND word_count > 200
```

To this:

```text
HIGH =
  transcript_available
  AND word_count >= 500
  AND meaningful_text_ratio >= 0.75
  AND supported_language = true
```

Then use `MEDIUM` for:

```text
transcript_available
AND word_count >= 200
AND meaningful_text_ratio >= 0.6
```

Only run **Deep Analysis** automatically on `HIGH`.

For `MEDIUM`, allow Standard or Quick analysis and show a warning.

For `LOW`, ask the user to provide another source or use metadata-only fallback.

---

## Best v0.3 Rule

```python
if not transcript_available:
    confidence = "unusable"

elif word_count >= 500 and meaningful_text_ratio >= 0.75 and supported_language:
    confidence = "high"

elif word_count >= 200 and meaningful_text_ratio >= 0.60 and supported_language:
    confidence = "medium"

elif word_count >= 100:
    confidence = "low"

else:
    confidence = "unusable"
```

This is much stronger than the current rule, but still simple enough for Cursor to implement safely.

---

## Final Judgement

Cursor's current logic is **acceptable for a prototype**, but it is **too weak for a product-quality source extraction confidence system**.

Keep it only if the immediate goal is:

```text
Can I get YouTube source analysis working quickly?
```

Improve it now if the goal is:

```text
Can AlphaBrief give users honest confidence about whether this video is analyzable?
```

For AlphaBrief, it is better to improve this now. This small backend decision affects UX, pricing limits, retry logic, fallback behavior, and whether users trust the generated brief.
