from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from app.core.enums import ResearchMode


@dataclass(frozen=True)
class SegmentAnalysisResult:
    analysis_markdown: str
    analysis_json: dict
    key_entities: list
    key_topics: list
    confidence_label: str
    input_tokens: int
    output_tokens: int


class AiProviderClient(Protocol):
    async def generate_segment_analysis(
        self, prompt: str, *, depth: ResearchMode
    ) -> SegmentAnalysisResult: ...


def estimated_input_tokens(prompt: str) -> int:
    # Rough, deterministic estimate (no external tokenizer).
    return max(1, len(prompt) // 4)


_META_ENTITIES = re.compile(r"^SEGMENT_ENTITIES_JSON:\s*(\[.*\])\s*$", re.MULTILINE)
_META_TOPICS = re.compile(r"^SEGMENT_TOPICS_JSON:\s*(\[.*\])\s*$", re.MULTILINE)


def _parse_json_list(pattern: re.Pattern[str], text: str) -> list:
    m = pattern.search(text)
    if not m:
        return []
    try:
        raw = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    return raw if isinstance(raw, list) else []


class MockAiProviderClient:
    """Deterministic mock for tests / local dev. Returns canned output
    derived from the prompt; does not call any external service."""

    async def generate_segment_analysis(
        self, prompt: str, *, depth: ResearchMode
    ) -> SegmentAnalysisResult:
        title = "Segment"
        for line in prompt.splitlines():
            if line.strip().startswith("## Segment:"):
                title = line.split("## Segment:", 1)[1].strip() or title
                break

        entities = _parse_json_list(_META_ENTITIES, prompt)
        topics = _parse_json_list(_META_TOPICS, prompt)

        context_brief = "Analysis mode: CONTEXT_BRIEF" in prompt
        disclosure = ""
        if context_brief:
            disclosure = (
                "\n\nFull source text was not available for this segment; "
                "findings rely on metadata and supplementary context.\n"
            )

        analysis_markdown = (
            f"## {title}\n\n"
            f"[Mock analysis at {depth.value} depth]\n\n"
            f"Key entities: {entities}\n\n"
            f"This is mock output for development.{disclosure}"
        )
        return SegmentAnalysisResult(
            analysis_markdown=analysis_markdown,
            analysis_json={
                "mock": True,
                "depth": depth.value,
                "title": title,
            },
            key_entities=list(entities),
            key_topics=list(topics),
            confidence_label="MEDIUM",
            input_tokens=estimated_input_tokens(prompt),
            output_tokens=500,
        )

