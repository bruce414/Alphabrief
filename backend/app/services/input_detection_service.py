"""Pure string-based detection of URLs and chat intent (no I/O)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urldefrag, urlparse

from app.core.enums import InputType, IntentType

# HTTP(S) URLs — conservative to avoid matching trailing punctuation.
_URL_RE = re.compile(
    r"https?://[^\s<>\[\]{}|\\^`\"']+",
    re.IGNORECASE,
)


def _strip_trailing_junk(url: str) -> str:
    return url.rstrip(").,;]'\"")


def extract_urls(message: str) -> list[str]:
    """Return distinct URLs in order of first appearance."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _URL_RE.finditer(message):
        u = _strip_trailing_junk(m.group(0))
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def classify_url_input_type(url: str) -> InputType:
    """Classify a single URL for storage / routing (matches v0.3 URL heuristics)."""
    fragless = urldefrag(url.strip())[0]
    p = urlparse(fragless)
    host = (p.hostname or "").lower()

    if host.endswith("sec.gov") or host.endswith("www.sec.gov"):
        return InputType.FILING_URL

    path_l = (p.path or "").lower()
    if host in {"youtu.be", "www.youtu.be"}:
        return InputType.YOUTUBE_URL
    if "youtube.com" in host or "youtube-nocookie.com" in host:
        if "/watch" in path_l or path_l.startswith("/watch"):
            return InputType.YOUTUBE_URL
        if "/shorts/" in path_l or path_l.startswith("/shorts/"):
            return InputType.YOUTUBE_URL

    return InputType.ARTICLE_URL


def _primary_input_type(per_url_types: list[InputType]) -> InputType:
    if not per_url_types:
        return InputType.QUESTION
    distinct = {t for t in per_url_types}
    if len(distinct) == 1:
        return next(iter(distinct))
    return InputType.MIXED


def _infer_intent(message: str, urls: list[str]) -> IntentType:
    lower = message.lower()
    if "generate a brief" in lower or "write a brief" in lower:
        return IntentType.BRIEF_GENERATION
    if "add to canvas" in lower or "summarize this area" in lower:
        return IntentType.CANVAS_ACTION
    if urls:
        return IntentType.SOURCE_ANALYSIS
    return IntentType.GENERAL_ASK


@dataclass(frozen=True)
class DetectedInput:
    urls: list[str]
    per_url_type: list[InputType]
    primary_input_type: InputType
    intent_type: IntentType


def detect_input(message: str) -> DetectedInput:
    urls = extract_urls(message)
    per_url_type = [classify_url_input_type(u) for u in urls]
    primary = _primary_input_type(per_url_type)
    intent = _infer_intent(message, urls)
    return DetectedInput(
        urls=urls,
        per_url_type=per_url_type,
        primary_input_type=primary,
        intent_type=intent,
    )
