from __future__ import annotations

import uuid

from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.project import Project
from app.models.source import Source
from app.services.chat_prompt_builder import PROMPT_MAX_CHARS, build_chat_prompt


def test_prompt_builder_truncates_oldest_history_first_and_trims_source_snippets():
    project = Project(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        kind="THESIS",
        title="Proj",
        description=None,
        archived_at=None,
        metadata_={},
    )
    chat = Chat(
        id=uuid.uuid4(),
        project_id=project.id,
        user_id=project.user_id,
        title="New chat",
        status="ACTIVE",
        last_turn_at=None,
        metadata_={},
    )

    # 20 turns of big history + final user message.
    prior_turns: list[ChatTurn] = []
    for i in range(20):
        prior_turns.append(
            ChatTurn(
                id=uuid.uuid4(),
                chat_id=chat.id,
                user_id=chat.user_id,
                turn_index=i,
                role="ASSISTANT" if i % 2 else "USER",
                status="COMPLETED",
                content_markdown=("H" * 6000) + f" idx={i}",
                content_json=None,
                model_provider=None,
                model_name=None,
            )
        )
    prior_turns.append(
        ChatTurn(
            id=uuid.uuid4(),
            chat_id=chat.id,
            user_id=chat.user_id,
            turn_index=21,
            role="USER",
            status="COMPLETED",
            content_markdown="Final user message",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )

    src = Source(
        id=uuid.uuid4(),
        user_id=chat.user_id,
        source_type="ARTICLE_URL",
        source_access_method="SERVER_FETCH",
        source_access_status="FULL_TEXT_EXTRACTED",
        original_input="https://example.com/a",
        normalized_url="https://example.com/a",
        canonical_url="https://example.com/a",
        file_key=None,
        file_name=None,
        mime_type=None,
        file_size_bytes=None,
        title="Example",
        publisher=None,
        author=None,
        published_at=None,
        extracted_text="X" * 2000,
        extracted_text_word_count=2000,
        extraction_confidence=None,
        extraction_error=None,
        raw_text_retention="NOT_STORED",
        content_hash=None,
        metadata_={},
        source_complexity=None,
        segment_count=None,
        scan_status=None,
    )

    prompt = build_chat_prompt(chat=chat, project=project, prior_turns=prior_turns, sources=[src])

    total = len(prompt.system) + len(prompt.user) + len(prompt.attached_sources_section) + sum(
        len(h["role"]) + len(h["content_markdown"]) for h in prompt.history
    )
    assert total <= PROMPT_MAX_CHARS

    # Oldest history should be dropped first when truncating.
    if prompt.history:
        assert "idx=0" not in prompt.history[0]["content_markdown"]

    # Source snippet should never exceed the 500-char rule when present.
    for line in prompt.attached_sources_section.splitlines():
        if line.startswith("- "):
            snippet = line.split(":", 1)[-1].strip()
            assert len(snippet) <= 520  # allow for "(no...)" or ellipsis overhead

