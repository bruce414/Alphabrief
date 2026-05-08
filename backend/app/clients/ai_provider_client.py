from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypedDict


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


class AiProviderClient(Protocol):
    async def generate_chat_reply(self, prompt: ChatPrompt) -> ChatReply: ...


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

