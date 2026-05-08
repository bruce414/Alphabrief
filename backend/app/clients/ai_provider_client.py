from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypedDict

from app.models.source import Source


@dataclass(frozen=True, slots=True)
class ChatPrompt:
    system: str
    history: list[dict[str, str]]  # {role, content_markdown} oldest→newest
    user: str
    attached_sources_section: str


class ChatReply(TypedDict):
    content_markdown: str
    content_json: dict
    input_tokens: int
    output_tokens: int


class CandidateExtraction(TypedDict):
    block_type: str
    title: str | None
    content_markdown: str


class AiProviderClient(Protocol):
    async def generate_chat_reply(self, prompt: ChatPrompt) -> ChatReply: ...
    async def extract_candidates(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        attached_sources: list[Source],
    ) -> list[CandidateExtraction]: ...


class MockAiProviderClient:
    async def generate_chat_reply(self, prompt: ChatPrompt) -> ChatReply:
        titles: list[str] = []
        for line in prompt.attached_sources_section.splitlines():
            if line.startswith("- "):
                # "- Title (url): snippet"
                title = line[2:].split(" (", 1)[0].strip()
                if title:
                    titles.append(title)

        user_stub = (prompt.user or "").strip().replace("\n", " ")[:120]
        titles_stub = ", ".join(titles) if titles else "none"

        content_markdown = (
            "## Mock reply\n\n"
            f"User message: {user_stub}\n\n"
            f"Attached sources: {titles_stub}\n\n"
            "This is a deterministic mock response (no real LLM call)."
        ).strip()

        # Cheap deterministic token estimates (stable for tests).
        input_tokens = max(1, len((prompt.system + prompt.user + prompt.attached_sources_section)) // 4)
        output_tokens = max(1, len(content_markdown) // 4)

        return {
            "content_markdown": content_markdown,
            "content_json": {"provider": "mock", "echo": {"user": user_stub, "source_titles": titles}},
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    async def extract_candidates(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        attached_sources: list[Source],
    ) -> list[CandidateExtraction]:
        # Deterministic test heuristic:
        # - one CLAIM per "### " header in assistant_reply (max 2)
        # - else: if assistant_reply > 200 chars, return 1 CLAIM titled by first 60 chars; otherwise empty
        reply = (assistant_reply or "").strip()
        if not reply:
            return []

        headers: list[str] = []
        for line in reply.splitlines():
            if line.startswith("### "):
                h = line[4:].strip()
                if h:
                    headers.append(h)

        candidates: list[CandidateExtraction] = []
        if headers:
            for h in headers[:2]:
                candidates.append(
                    {
                        "block_type": "CLAIM",
                        "title": h[:120],
                        "content_markdown": f"{h}",
                    }
                )
            return candidates

        if len(reply) > 200:
            title = reply.replace("\n", " ")[:60].strip() or None
            return [
                {
                    "block_type": "CLAIM",
                    "title": title,
                    "content_markdown": reply[:400].strip() or reply,
                }
            ]

        return []

