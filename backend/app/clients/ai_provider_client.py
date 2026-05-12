from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol, TypedDict

from app.core.enums import ResearchMode
from app.models.source import Source


@dataclass(frozen=True, slots=True)
class ChatPrompt:
    system: str
    history: list[dict[str, str]]  # {role, content_markdown} oldest→newest
    user: str
    attached_sources_section: str


# A single research-process event emitted while the assistant is thinking.
# Shape examples:
#   {"type": "search", "query": "gold market 2026", "status": "running"}
#   {"type": "search", "query": "gold market 2026", "status": "done", "resultCount": 5}
#   {"type": "read", "url": "https://ft.com/...", "title": "Gold spot prices", "snippet": "..."}
#   {"type": "thinking", "text": "Considering supply vs demand..."}
ResearchEvent = dict[str, Any]
EventCallback = Callable[[ResearchEvent], Awaitable[None]]


class ChatReply(TypedDict):
    content_markdown: str
    content_json: dict
    input_tokens: int
    output_tokens: int
    # Each entry: {"url": str, "title": str | None, "snippet": str | None, "publisher": str | None}
    web_search_results: list[dict]


class CandidateExtraction(TypedDict, total=False):
    suggested_element_type: str
    title: str | None
    content_markdown: str
    suggested_position: dict[str, float] | None


class MemoryRefresh(TypedDict, total=False):
    summary_markdown: str
    entities: list[str]
    themes: list[str]
    open_questions: list[str]
    conclusions: list[str]


async def _noop_event_callback(event: ResearchEvent) -> None:  # pragma: no cover - default
    return None


class AiProviderClient(Protocol):
    async def generate_chat_reply(
        self,
        prompt: ChatPrompt,
        *,
        research_mode: ResearchMode = ResearchMode.STANDARD,
        on_event: EventCallback = _noop_event_callback,
    ) -> ChatReply: ...

    async def generate_chat_title(
        self,
        *,
        user_message: str,
        assistant_reply: str,
    ) -> str: ...

    async def extract_candidates(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        attached_sources: list[Source],
    ) -> list[CandidateExtraction]: ...

    async def refresh_project_memory(
        self,
        *,
        project_title: str,
        current_memory_summary: str | None,
        recent_turns_markdown: list[str],
    ) -> MemoryRefresh: ...


class MockAiProviderClient:
    async def generate_chat_reply(
        self,
        prompt: ChatPrompt,
        *,
        research_mode: ResearchMode = ResearchMode.STANDARD,
        on_event: EventCallback = _noop_event_callback,
    ) -> ChatReply:
        titles: list[str] = []
        for line in prompt.attached_sources_section.splitlines():
            if line.startswith("- "):
                # "- Title (url): snippet"
                title = line[2:].split(" (", 1)[0].strip()
                if title:
                    titles.append(title)

        user_stub = (prompt.user or "").strip().replace("\n", " ")[:120]
        titles_stub = ", ".join(titles) if titles else "none"

        # Emit a couple of synthetic events so the UI can be exercised against the mock.
        if research_mode != ResearchMode.QUICK:
            await on_event({"type": "search", "query": user_stub[:60] or "context", "status": "running"})
            await on_event({"type": "search", "query": user_stub[:60] or "context", "status": "done", "resultCount": 0})

        content_markdown = (
            "## Mock reply\n\n"
            f"User message: {user_stub}\n\n"
            f"Attached sources: {titles_stub}\n\n"
            "This is a deterministic mock response (no real LLM call).\n\n"
            "---\n\n"
            "### Key entities\n"
            "- MOCK_CO (MOCK)\n"
            "- Example Index (XLK)\n\n"
            "---\n\n"
            "### Canvas insight cards\n"
            '- {"elementType":"CLAIM","title":"Mock claim","contentMarkdown":"Mock insight from the reply."}\n'
            '- {"elementType":"QUESTION","title":"","contentMarkdown":"What would validate this next?"}\n\n'
            "---\n\n"
            "### Follow-up questions\n"
            "- What angle should we explore next?\n"
            "- Which risk factor matters most for this topic?\n"
        ).strip()

        # Cheap deterministic token estimates (stable for tests).
        input_tokens = max(1, len((prompt.system + prompt.user + prompt.attached_sources_section)) // 4)
        output_tokens = max(1, len(content_markdown) // 4)

        return {
            "content_markdown": content_markdown,
            "content_json": {"provider": "mock", "echo": {"user": user_stub, "source_titles": titles}},
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "web_search_results": [],
        }

    async def generate_chat_title(
        self,
        *,
        user_message: str,
        assistant_reply: str,
    ) -> str:
        words = (user_message or "").strip().split()
        if not words:
            return "New chat"
        title = " ".join(words[:6])
        # Title-case but preserve common acronyms by only touching lowercase-only tokens.
        return title[:60].strip(" .,;:!?-") or "New chat"

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
            for idx, h in enumerate(headers[:2]):
                element_type = "CLAIM" if idx == 0 else "QUESTION"
                candidates.append(
                    {
                        "suggested_element_type": element_type,
                        "title": h[:120],
                        "content_markdown": f"{h}",
                        "suggested_position": {
                            "x": 320.0 + 360.0 * idx,
                            "y": 240.0,
                            "width": 320.0,
                            "height": 180.0,
                        },
                    }
                )
            return candidates

        if len(reply) > 200:
            title = reply.replace("\n", " ")[:60].strip() or None
            return [
                {
                    "suggested_element_type": "CLAIM",
                    "title": title,
                    "content_markdown": reply[:400].strip() or reply,
                    "suggested_position": {
                        "x": 320.0,
                        "y": 240.0,
                        "width": 320.0,
                        "height": 180.0,
                    },
                }
            ]

        return []

    async def refresh_project_memory(
        self,
        *,
        project_title: str,
        current_memory_summary: str | None,
        recent_turns_markdown: list[str],
    ) -> MemoryRefresh:
        _ = current_memory_summary
        _ = recent_turns_markdown
        return {
            "summary_markdown": f"Mock memory summary for {project_title}",
            "entities": ["MOCK"],
            "themes": ["mock-theme"],
            "open_questions": ["What is the next milestone?"],
            "conclusions": [],
        }


def get_ai_provider_client() -> AiProviderClient:
    from app.core.config import settings  # local import to avoid circular deps

    if settings.ai_provider == "anthropic" and settings.anthropic_api_key:
        from app.clients.anthropic_client import AnthropicClient

        return AnthropicClient()
    return MockAiProviderClient()
