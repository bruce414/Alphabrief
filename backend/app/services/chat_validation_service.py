from __future__ import annotations

import re
from dataclasses import dataclass

import bleach

from app.models.source import Source


ALLOWED_TAGS = [
    "p",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "h1",
    "h2",
    "h3",
    "code",
    "blockquote",
    "a",
]

REJECT_RE = re.compile(
    r"\bbuy this\b|\bguaranteed (return|profit)\b|\byou should (invest|buy)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ChatValidationResult:
    content_markdown: str
    warnings: list[str]


def validate_chat_reply(*, content_markdown: str, attached_sources: list[Source]) -> ChatValidationResult:
    if not content_markdown or not content_markdown.strip():
        raise ValueError("Empty assistant reply")

    if REJECT_RE.search(content_markdown):
        raise ValueError("Disallowed advice phrase detected")

    cleaned = bleach.clean(
        content_markdown,
        tags=ALLOWED_TAGS,
        attributes={"a": ["href", "title"]},
        strip=True,
    ).strip()

    if not cleaned:
        raise ValueError("Reply became empty after sanitization")

    warnings: list[str] = []
    if any(s.source_access_status == "METADATA_ONLY" for s in attached_sources):
        # Soft check in this PR: warn only (PR #15 tightens).
        lowered = cleaned.lower()
        if "full source text was unavailable" not in lowered and "full text was unavailable" not in lowered:
            warnings.append("METADATA_ONLY source attached; reply did not mention full text was unavailable")

    return ChatValidationResult(content_markdown=cleaned, warnings=warnings)

