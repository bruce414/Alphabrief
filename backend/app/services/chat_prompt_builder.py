from __future__ import annotations

from dataclasses import dataclass

from app.clients.ai_provider_client import ChatPrompt
from app.models.chat import Chat
from app.models.project import Project
from app.models.source import Source
from app.models.chat_turn import ChatTurn


# Inline constant per PR #9b prompt.
PROMPT_MAX_CHARS = 80_000


def _source_display_url(src: Source) -> str:
    return (src.canonical_url or src.normalized_url or src.original_input or "").strip()


def _source_display_title(src: Source) -> str:
    return (src.title or "Untitled source").strip()


def _truncate(s: str, n: int) -> str:
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def build_chat_prompt(*, chat: Chat, project: Project, prior_turns: list[ChatTurn], sources: list[Source]) -> ChatPrompt:
    system = (
        "You are AlphaBrief, a market research assistant.\n"
        "You provide educational, informational analysis — not personalized financial advice.\n"
        "Be clear about uncertainty, avoid guarantees, and do not tell the user to buy/sell/invest.\n"
        f"Project: {project.title}\n"
    ).strip()

    # Expect `prior_turns` oldest→newest and to include the current user turn as the last USER message.
    cleaned_turns: list[dict[str, str]] = []
    for t in prior_turns:
        content = (t.content_markdown or "").strip()
        if not content:
            continue
        cleaned_turns.append({"role": t.role, "content_markdown": content})

    user_message = ""
    history: list[dict[str, str]] = []
    if cleaned_turns and cleaned_turns[-1]["role"] == "USER":
        user_message = cleaned_turns[-1]["content_markdown"]
        history = cleaned_turns[:-1]
    else:
        # Fallback: treat the newest USER turn as the message; everything before it is history.
        for i in range(len(cleaned_turns) - 1, -1, -1):
            if cleaned_turns[i]["role"] == "USER":
                user_message = cleaned_turns[i]["content_markdown"]
                history = cleaned_turns[:i] + cleaned_turns[i + 1 :]
                break

    # Build attached sources section with 500-char snippet rule.
    snippet_limit = 500
    lines = ["## Attached sources"]
    for src in sources:
        url = _source_display_url(src)
        title = _source_display_title(src)
        snippet = (src.extracted_text or "").strip()
        snippet = _truncate(snippet, snippet_limit) if snippet else ""
        tail = f": {snippet}" if snippet else ": (no extracted text available)"
        lines.append(f"- {title} ({url}){tail}")
    attached_sources_section = "\n".join(lines).strip()

    prompt = ChatPrompt(
        system=system,
        history=history,
        user=user_message,
        attached_sources_section=attached_sources_section,
    )

    # Cap total prompt. Drop oldest history first, then trim source snippets.
    def prompt_len(p: ChatPrompt) -> int:
        return len(p.system) + len(p.user) + len(p.attached_sources_section) + sum(
            len(h.get("role", "")) + len(h.get("content_markdown", "")) for h in p.history
        )

    while prompt_len(prompt) > PROMPT_MAX_CHARS and prompt.history:
        prompt.history.pop(0)

    if prompt_len(prompt) > PROMPT_MAX_CHARS and sources:
        # Rebuild attached sources section with progressively smaller snippet budget.
        # Keep user message and source titles/URLs.
        for snippet_limit in (250, 120, 60, 0):
            lines = ["## Attached sources"]
            for src in sources:
                url = _source_display_url(src)
                title = _source_display_title(src)
                snippet = (src.extracted_text or "").strip()
                if snippet_limit <= 0:
                    tail = ": (snippet omitted)"
                else:
                    snippet = _truncate(snippet, snippet_limit) if snippet else ""
                    tail = f": {snippet}" if snippet else ": (no extracted text available)"
                lines.append(f"- {title} ({url}){tail}")
            prompt = ChatPrompt(
                system=prompt.system,
                history=prompt.history,
                user=prompt.user,
                attached_sources_section="\n".join(lines).strip(),
            )
            if prompt_len(prompt) <= PROMPT_MAX_CHARS:
                break

    if prompt_len(prompt) > PROMPT_MAX_CHARS:
        # Last resort: truncate user message (priority says keep it, but must obey hard cap).
        budget = max(0, PROMPT_MAX_CHARS - (len(prompt.system) + len(prompt.attached_sources_section)))
        prompt = ChatPrompt(
            system=prompt.system,
            history=[],
            user=_truncate(prompt.user, max(0, budget)),
            attached_sources_section=prompt.attached_sources_section,
        )

    return prompt

