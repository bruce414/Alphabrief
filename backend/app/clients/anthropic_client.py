"""Anthropic Claude client for AlphaBrief v0.3."""

from __future__ import annotations

import json
import logging
from typing import Any, cast

from anthropic import AsyncAnthropic
from anthropic.types import ToolParam
from fastapi import status

from app.clients.ai_provider_client import (
    AiProviderClient,
    CandidateExtraction,
    ChatPrompt,
    ChatReply,
    EventCallback,
    ExistingCanvasElement,
    MemoryRefresh,
    _noop_event_callback,
)
from app.core.config import settings
from app.core.errors import AppError
from app.core.enums import ResearchMode
from app.models.source import Source

logger = logging.getLogger(__name__)


def _custom_tool(*, name: str, input_schema: dict[str, Any]) -> ToolParam:
    """Build a typed custom-tool definition for Anthropic messages.create."""
    return cast(
        ToolParam,
        {
            "name": name,
            "input_schema": input_schema,
        },
    )


# Anthropic server-side web search tool spec. The dated identifier is required.
_WEB_SEARCH_TOOL_TYPE = "web_search_20250305"
_WEB_SEARCH_TOOL_NAME = "web_search"


def _web_search_tool(research_mode: ResearchMode) -> dict[str, Any] | None:
    """Return a web_search tool spec for non-QUICK modes; None when search should be skipped."""
    if research_mode == ResearchMode.QUICK:
        return None
    max_uses = 8 if research_mode == ResearchMode.DEEP else 4
    return {
        "type": _WEB_SEARCH_TOOL_TYPE,
        "name": _WEB_SEARCH_TOOL_NAME,
        "max_uses": max_uses,
    }


def _extract_text(block: Any) -> str:
    text = getattr(block, "text", None)
    if isinstance(text, str):
        return text
    return ""


class AnthropicClient(AiProviderClient):
    async def generate_chat_reply(
        self,
        prompt: ChatPrompt,
        *,
        research_mode: ResearchMode = ResearchMode.STANDARD,
        on_event: EventCallback = _noop_event_callback,
    ) -> ChatReply:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        messages: list[dict[str, Any]] = []
        for turn in prompt.history:
            role = turn.get("role")
            if role == "USER":
                anthropic_role = "user"
            elif role == "ASSISTANT":
                anthropic_role = "assistant"
            else:
                raise ValueError(f"Unsupported role in history: {role!r}")
            messages.append(
                {
                    "role": anthropic_role,
                    "content": turn.get("content_markdown", ""),
                }
            )

        attached = (prompt.attached_sources_section or "").strip()
        if attached:
            user_content = (prompt.user or "") + "\n\n" + prompt.attached_sources_section
        else:
            user_content = prompt.user or ""
        messages.append({"role": "user", "content": user_content})

        system = [
            {
                "type": "text",
                "text": prompt.system,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        tools: list[dict[str, Any]] = []
        web_tool = _web_search_tool(research_mode)
        if web_tool is not None:
            tools.append(web_tool)

        create_kwargs: dict[str, Any] = {
            "model": settings.anthropic_model,
            "max_tokens": settings.chat_max_output_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            create_kwargs["tools"] = tools

        # Stream so we can surface intermediate research events. Anthropic emits
        # content_block_start/delta/stop events; we track web_search tool_use blocks
        # (the queries) and web_search_tool_result blocks (the results) separately.
        text_parts: list[str] = []
        web_search_results: list[dict[str, Any]] = []
        # Map block index → accumulator state.
        # For server_tool_use: {"type": "search", "query_json": str_accumulator, "tool_use_id": id}
        block_state: dict[int, dict[str, Any]] = {}

        input_tokens = 0
        output_tokens = 0

        try:
            async with client.messages.stream(**create_kwargs) as stream:
                async for event in stream:
                    etype = getattr(event, "type", None)

                    if etype == "content_block_start":
                        index = int(getattr(event, "index", 0))
                        block = getattr(event, "content_block", None)
                        btype = getattr(block, "type", None)

                        if btype == "server_tool_use" and getattr(block, "name", None) == _WEB_SEARCH_TOOL_NAME:
                            block_state[index] = {
                                "type": "search",
                                "query_json": "",
                                "tool_use_id": getattr(block, "id", None),
                            }
                            # Emit a pending search event (query filled on stop).
                            await on_event({"type": "search", "status": "running", "query": None})

                        elif btype == "web_search_tool_result":
                            results_raw = getattr(block, "content", None)
                            # `content` is either a list of WebSearchResultBlock or a
                            # WebSearchToolResultError; ignore the latter for the events
                            # log (the search itself was already marked failed).
                            if not isinstance(results_raw, list):
                                results_raw = []
                            parsed: list[dict[str, Any]] = []
                            for item in results_raw:
                                # `item` may be a dict-like model. Use attribute or key access defensively.
                                url = _get(item, "url")
                                title = _get(item, "title")
                                page_age = _get(item, "page_age")
                                if not isinstance(url, str) or not url:
                                    continue
                                entry = {
                                    "url": url,
                                    "title": title if isinstance(title, str) else None,
                                    "publisher": _hostname(url),
                                    "pageAge": page_age if isinstance(page_age, str) else None,
                                }
                                parsed.append(entry)
                                if entry not in web_search_results:
                                    web_search_results.append(entry)
                                await on_event(
                                    {
                                        "type": "read",
                                        "url": entry["url"],
                                        "title": entry["title"],
                                        "publisher": entry["publisher"],
                                    }
                                )

                    elif etype == "content_block_delta":
                        index = int(getattr(event, "index", 0))
                        delta = getattr(event, "delta", None)
                        dtype = getattr(delta, "type", None)
                        if dtype == "text_delta":
                            text_parts.append(getattr(delta, "text", "") or "")
                        elif dtype == "input_json_delta":
                            partial = getattr(delta, "partial_json", "") or ""
                            state = block_state.get(index)
                            if state is not None and state.get("type") == "search":
                                state["query_json"] = (state.get("query_json") or "") + partial

                    elif etype == "content_block_stop":
                        index = int(getattr(event, "index", 0))
                        state = block_state.get(index)
                        if state is not None and state.get("type") == "search":
                            query = None
                            try:
                                parsed_q = json.loads(state.get("query_json") or "{}")
                                if isinstance(parsed_q, dict):
                                    q = parsed_q.get("query")
                                    if isinstance(q, str) and q.strip():
                                        query = q.strip()
                            except json.JSONDecodeError:
                                query = None
                            await on_event(
                                {
                                    "type": "search",
                                    "status": "done",
                                    "query": query,
                                }
                            )

                # `final_message()` returns the assembled Message; usage is on it.
                final_message = await stream.get_final_message()
                usage = getattr(final_message, "usage", None)
                input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
                output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        except Exception:
            logger.exception("Anthropic streaming failed")
            raise

        content_markdown = "".join(text_parts).strip()
        if not content_markdown:
            raise ValueError("Empty response from Anthropic")

        return {
            "content_markdown": content_markdown,
            "content_json": {
                "provider": "anthropic",
                "model": settings.anthropic_model,
                "researchMode": research_mode.value,
            },
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "web_search_results": web_search_results,
        }

    async def generate_chat_title(
        self,
        *,
        user_message: str,
        assistant_reply: str,
    ) -> str:
        user_message = (user_message or "").strip()
        assistant_reply = (assistant_reply or "").strip()
        if not user_message and not assistant_reply:
            return "New chat"

        try:
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            system = (
                "You produce a very short chat title that summarizes the topic. "
                "Rules: 3 to 6 words, Title Case, no quotes, no trailing punctuation, "
                "no leading 'Chat about' / 'Discussion of'. Output ONLY the title text."
            )
            content = (
                f"User message:\n{user_message[:1200]}\n\n"
                f"Assistant reply:\n{assistant_reply[:1200]}"
            )
            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=40,
                system=system,
                messages=[{"role": "user", "content": content}],
            )
            for block in getattr(response, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    text = (getattr(block, "text", None) or "").strip()
                    if text:
                        # Strip wrapping quotes/backticks and trailing punctuation.
                        cleaned = text.strip().strip('"').strip("'").strip("`").strip()
                        cleaned = cleaned.rstrip(" .,;:!?-")
                        cleaned = " ".join(cleaned.split())  # collapse whitespace
                        return cleaned[:80] or "New chat"
        except Exception:
            logger.warning("Anthropic title generation failed; falling back", exc_info=True)

        # Fallback: first 6 words of the user message.
        words = user_message.split()
        return (" ".join(words[:6]) or "New chat")[:80]

    async def extract_candidates(
        self,
        *,
        user_message: str,
        assistant_reply: str,
        attached_sources: list[Source],
        existing_canvas_elements: list[ExistingCanvasElement] | None = None,
    ) -> list[CandidateExtraction]:
        _ = attached_sources
        elements = existing_canvas_elements or []

        def _format_existing_elements_for_prompt(
            canvas_elements: list[ExistingCanvasElement],
        ) -> str:
            if not canvas_elements:
                return "Existing canvas elements: (none — omit proposed_edge)\n\n"
            lines = [
                "Existing canvas elements (proposed_edge.target_title must match one of these titles exactly):"
            ]
            for el in canvas_elements[:40]:
                et = el.get("element_type") or "TEXT"
                lines.append(f'- [{et}] {el.get("title", "")}')
            return "\n".join(lines) + "\n\n"
        try:
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)

            tool_schema = _custom_tool(
                name="add_canvas_candidates",
                input_schema={
                    "type": "object",
                    "properties": {
                        "candidates": {
                            "type": "array",
                            "maxItems": 2,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "kind": {
                                        "type": "string",
                                        "enum": ["CLAIM", "RISK", "EVIDENCE", "QUESTION"],
                                    },
                                    "title": {"type": ["string", "null"]},
                                    "body": {"type": "string"},
                                    "proposed_edge": {
                                        "type": ["object", "null"],
                                        "properties": {
                                            "edge_type": {
                                                "type": "string",
                                                "enum": ["supports", "contradicts", "affects"],
                                            },
                                            "target_title": {"type": "string"},
                                        },
                                        "required": ["edge_type", "target_title"],
                                        "additionalProperties": False,
                                    },
                                },
                                "required": ["kind", "body"],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["candidates"],
                    "additionalProperties": False,
                },
            )

            system = (
                "Extract canvas card candidates from the conversation. "
                "Return AT MOST 2 candidates. "
                "Each candidate must be exactly one of: CLAIM, RISK, EVIDENCE, QUESTION. "
                "Definitions: CLAIM = debatable statement that needs evidence. "
                "RISK = a potential negative uncertainty or downside factor. "
                "EVIDENCE = a specific source-backed data point. "
                "QUESTION = an unresolved research gap. "
                "If you cannot produce a CLEARLY worth-keeping candidate from the conversation, "
                "return an empty list. Bias toward FEWER, BETTER candidates. "
                "For each candidate you may include at most one proposed_edge linking the new "
                "candidate to an existing canvas element (usually the DIRECTION node or an "
                "existing claim) by that element's title. Use edge_type supports, contradicts, "
                "or affects. Omit proposed_edge when no clear relationship exists. "
                "Output JSON shape: { candidates: [{ kind, title, body, proposed_edge? }] }."
            )

            canvas_section = _format_existing_elements_for_prompt(elements)
            user_content = (
                f"{canvas_section}"
                f"User message:\n{user_message}\n\n"
                f"Assistant reply:\n{assistant_reply}"
            )

            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=1024,
                system=system,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": "add_canvas_candidates"},
                messages=[{"role": "user", "content": user_content}],
            )

            tool_input = None
            for block in getattr(response, "content", []) or []:
                if (
                    getattr(block, "type", None) == "tool_use"
                    and getattr(block, "name", None) == "add_canvas_candidates"
                ):
                    tool_input = getattr(block, "input", None)
                    break

            if not isinstance(tool_input, dict):
                logger.warning("Anthropic candidate extraction returned no tool_use input")
                return []

            candidates = tool_input.get("candidates", [])
            if not isinstance(candidates, list):
                logger.warning("Anthropic candidate extraction tool input missing candidates array")
                return []

            normalized: list[CandidateExtraction] = []
            for raw in candidates:
                if not isinstance(raw, dict):
                    continue
                kind = (raw.get("kind") or raw.get("suggested_element_type") or "").strip().upper()
                body = (raw.get("body") or raw.get("content_markdown") or "").strip()
                title_raw = raw.get("title")
                title = (
                    title_raw.strip()[:500]
                    if isinstance(title_raw, str) and title_raw.strip()
                    else None
                )
                if not kind or not body:
                    continue
                entry: CandidateExtraction = {
                    "suggested_element_type": kind,
                    "title": title,
                    "content_markdown": body,
                }
                proposed_edge = raw.get("proposed_edge")
                if isinstance(proposed_edge, dict):
                    edge_type = str(proposed_edge.get("edge_type") or "").strip().lower()
                    target_title_raw = proposed_edge.get("target_title")
                    target_title = (
                        target_title_raw.strip()
                        if isinstance(target_title_raw, str) and target_title_raw.strip()
                        else ""
                    )
                    if edge_type and target_title:
                        entry["proposed_edge"] = {
                            "edge_type": edge_type,
                            "target_title": target_title,
                        }
                # TODO: legacy confidence/importance fields are no longer extracted; default NULL if reintroduced.
                normalized.append(entry)
            return normalized
        except Exception:
            logger.warning("Anthropic candidate extraction failed", exc_info=True)
            return []

    async def suggest_research_directions(
        self,
        description: str,
        *,
        on_event: EventCallback = _noop_event_callback,
    ) -> list[dict[str, Any]]:
        _ = on_event
        try:
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)

            starter_item_schema = {
                "type": "object",
                "properties": {
                    "elementType": {"type": "string", "enum": ["STICKY_NOTE"]},
                    "provenanceKind": {"type": "string", "enum": ["AI_ONBOARDING"]},
                    "kind": {"type": "string", "enum": ["CLAIM", "RISK", "EVIDENCE", "QUESTION"]},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["elementType", "provenanceKind", "kind", "title", "body"],
                "additionalProperties": False,
            }

            direction_schema = {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "researchGoal": {"type": "string"},
                    "includedTopics": {"type": "array", "items": {"type": "string"}},
                    "excludedTopics": {"type": "array", "items": {"type": "string"}},
                    "targetEntities": {"type": "array", "items": {"type": "string"}},
                    "timeHorizon": {"type": ["string", "null"]},
                    "starterElements": {
                        "type": "array",
                        "minItems": 3,
                        "maxItems": 5,
                        "items": starter_item_schema,
                    },
                },
                "required": [
                    "key",
                    "title",
                    "summary",
                    "researchGoal",
                    "includedTopics",
                    "excludedTopics",
                    "targetEntities",
                    "starterElements",
                ],
                "additionalProperties": False,
            }

            tool_schema = _custom_tool(
                name="suggest_research_directions",
                input_schema={
                    "type": "object",
                    "properties": {
                        "directions": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 3,
                            "items": direction_schema,
                        }
                    },
                    "required": ["directions"],
                    "additionalProperties": False,
                },
            )

            system = (
                "You help finance researchers pick a focused direction. Given a short intent, "
                "return exactly 3 distinct research directions. Each direction needs a slug key, "
                "concise title (≤70 chars), 1-2 sentence summary, researchGoal, topic/entity scope "
                "lists, optional timeHorizon, and 3-5 starterElements (STICKY_NOTE with kind "
                "CLAIM|RISK|EVIDENCE|QUESTION). Educational research framing only — no buy/sell advice."
            )

            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=4096,
                system=system,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": "suggest_research_directions"},
                messages=[{"role": "user", "content": description.strip()}],
            )

            tool_input: Any = None
            for block in getattr(response, "content", []) or []:
                if (
                    getattr(block, "type", None) == "tool_use"
                    and getattr(block, "name", None) == "suggest_research_directions"
                ):
                    tool_input = getattr(block, "input", None)
                    break

            if not isinstance(tool_input, dict):
                logger.warning("Anthropic onboarding suggest returned no tool_use input")
                raise ValueError("missing tool_use input")

            directions = tool_input.get("directions")
            if not isinstance(directions, list) or len(directions) != 3:
                raise ValueError("expected exactly 3 directions")

            return directions  # type: ignore[return-value]
        except Exception:
            logger.warning("Anthropic research direction suggestion failed", exc_info=True)
            raise

    async def refresh_project_memory(
        self,
        *,
        project_title: str,
        current_memory_summary: str | None,
        recent_turns_markdown: list[str],
    ) -> MemoryRefresh:
        try:
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)

            tool_schema = _custom_tool(
                name="update_project_memory",
                input_schema={
                    "type": "object",
                    "properties": {
                        "summary_markdown": {"type": "string"},
                        "entities": {"type": "array", "items": {"type": "string"}},
                        "themes": {"type": "array", "items": {"type": "string"}},
                        "open_questions": {"type": "array", "items": {"type": "string"}},
                        "conclusions": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "summary_markdown",
                        "entities",
                        "themes",
                        "open_questions",
                        "conclusions",
                    ],
                    "additionalProperties": True,
                },
            )

            system = (
                "Update the project memory based on recent research activity. Summarize what the user is "
                "exploring, extract entity tickers/names mentioned, identify recurring themes, surface open "
                "research questions, and capture any tentative conclusions. Be specific and factual — never "
                "personalized investment advice."
            )

            summary_block = (current_memory_summary or "").strip() or "(none)"
            turns_blocks = "\n\n---\n\n".join(recent_turns_markdown) if recent_turns_markdown else "(none)"
            user_content = (
                f"Project title:\n{project_title}\n\n"
                f"## Current project memory\n{summary_block}\n\n"
                f"## Recent conversation (oldest first)\n{turns_blocks}"
            )

            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=2048,
                system=system,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": "update_project_memory"},
                messages=[{"role": "user", "content": user_content}],
            )

            tool_input: Any = None
            for block in getattr(response, "content", []) or []:
                if (
                    getattr(block, "type", None) == "tool_use"
                    and getattr(block, "name", None) == "update_project_memory"
                ):
                    tool_input = getattr(block, "input", None)
                    break

            if not isinstance(tool_input, dict):
                logger.warning("Anthropic memory refresh returned no tool_use input")
                raise ValueError("missing tool_use input")

            out: MemoryRefresh = {}
            sm = tool_input.get("summary_markdown")
            if isinstance(sm, str) and sm.strip():
                out["summary_markdown"] = sm.strip()

            for td_key, raw_key in (
                ("entities", "entities"),
                ("themes", "themes"),
                ("open_questions", "open_questions"),
                ("conclusions", "conclusions"),
            ):
                raw = tool_input.get(raw_key)
                if isinstance(raw, list):
                    cleaned = [str(x).strip() for x in raw if str(x).strip()]
                    if cleaned:
                        out[td_key] = cleaned  # type: ignore[literal-required]

            return out
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Anthropic memory refresh failed")
            raise AppError(
                error_code="MEMORY_REFRESH_FAILED",
                message="Could not refresh project memory from the AI provider.",
                status_code=status.HTTP_502_BAD_GATEWAY,
            ) from exc

    async def generate_quick_chat_analysis_json(
        self,
        *,
        system: str,
        user_content: str,
        prior_assistant_content: str | None = None,
        follow_up_user_content: str | None = None,
    ) -> str:
        try:
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            messages: list[dict[str, str]] = [{"role": "user", "content": user_content}]
            if prior_assistant_content is not None and follow_up_user_content is not None:
                messages.append(
                    {"role": "assistant", "content": prior_assistant_content},
                )
                messages.append({"role": "user", "content": follow_up_user_content})

            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=settings.chat_max_output_tokens,
                system=system,
                messages=messages,
            )
            for block in getattr(response, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    text = (getattr(block, "text", None) or "").strip()
                    if text:
                        return text
            raise ValueError("Empty response from Anthropic")
        except Exception:
            logger.exception("Anthropic quick chat analysis failed")
            raise


def _get(obj: Any, key: str) -> Any:
    """Attribute or dict-key access tolerant to both."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _hostname(url: str) -> str | None:
    try:
        from urllib.parse import urlparse

        host = urlparse(url).hostname or None
        if host and host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return None
