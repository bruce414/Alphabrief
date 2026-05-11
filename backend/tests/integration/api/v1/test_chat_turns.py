import pytest

import asyncio
from datetime import UTC, datetime, timedelta
import uuid
from uuid import UUID

from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.enums import ChatTurnRole, ChatTurnStatus
from app.models.chat_turn import ChatTurn
from app.models.source import Source
from app.repositories.chat_turn_repository import ChatTurnRepository
from app.repositories.chat_turn_source_repository import ChatTurnSourceRepository
from app.services.chat_turn_orchestrator import sweep_orphaned_turns_in_session


@pytest.mark.asyncio
async def test_list_chat_turns_returns_in_turn_index_order(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "turns1@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "T"})
    assert chat.status_code == 201
    chat_id = chat.json()["id"]

    me = await client.get("/api/v1/me")
    assert me.status_code == 200
    user_id = me.json()["id"]

    repo = ChatTurnRepository(db_session)
    t2 = await repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=2,
            role=ChatTurnRole.USER.value,
            status=ChatTurnStatus.COMPLETED.value,
            content_markdown="two",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )
    t0 = await repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=0,
            role=ChatTurnRole.USER.value,
            status=ChatTurnStatus.COMPLETED.value,
            content_markdown="zero",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )
    assert t0.id is not None
    assert t2.id is not None

    listed = await client.get(f"/api/v1/chats/{chat_id}/turns")
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert [i["turnIndex"] for i in items] == [0, 2]
    assert [i["contentMarkdown"] for i in items] == ["zero", "two"]


@pytest.mark.asyncio
async def test_chat_turn_cross_user_access_returns_403(client):
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "turnowner@example.com", "password": "password123"},
    )
    assert reg1.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "T"})
    chat_id = chat.json()["id"]

    await client.post("/api/v1/auth/logout")

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "turnother@example.com", "password": "password123"},
    )
    assert reg2.status_code == 201

    listed = await client.get(f"/api/v1/chats/{chat_id}/turns")
    assert listed.status_code == 403
    assert listed.json()["errorCode"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_repository_round_trip_including_chat_turn_sources(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "turnsources@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    me = await client.get("/api/v1/me")
    assert me.status_code == 200
    user_id = me.json()["id"]

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "T"})
    chat_id = chat.json()["id"]

    # Insert a Source directly; no need to go through API here.
    src = Source(
        user_id=user_id,
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
        publisher="ExamplePub",
        author=None,
        published_at=None,
        extracted_text=None,
        extracted_text_word_count=None,
        extraction_confidence=None,
        extraction_error=None,
        raw_text_retention="NOT_STORED",
        content_hash=None,
        metadata_={},
        source_complexity=None,
        segment_count=None,
        scan_status=None,
    )
    db_session.add(src)
    await db_session.commit()
    await db_session.refresh(src)

    turn_repo = ChatTurnRepository(db_session)
    turn = await turn_repo.create(
        ChatTurn(
            chat_id=chat_id,
            user_id=user_id,
            turn_index=0,
            role=ChatTurnRole.USER.value,
            status=ChatTurnStatus.COMPLETED.value,
            content_markdown="hi",
            content_json=None,
            model_provider=None,
            model_name=None,
        )
    )

    # Attach explicitly via join table (avoid async lazy-load).
    join_repo = ChatTurnSourceRepository(db_session)
    await join_repo.attach(chat_turn_id=turn.id, source_id=src.id)
    rows = await join_repo.list_for_turn(chat_turn_id=turn.id)
    assert len(rows) == 1
    assert rows[0].chat_turn_id == turn.id
    assert rows[0].source_id == src.id

    got = await client.get(f"/api/v1/chat-turns/{turn.id}")
    assert got.status_code == 200
    assert got.json()["id"] == str(turn.id)


@pytest.mark.asyncio
async def test_send_chat_message_no_sources_creates_turns_and_completes_assistant(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "send1@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    chat_id = chat.json()["id"]

    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Hello there"})
    assert sent.status_code == 200
    payload = sent.json()
    assert payload["detectedInputType"] == "QUESTION"
    assert payload["detectedIntentType"] == "GENERAL_ASK"
    assert payload["createdSourceIds"] == []
    assert payload["requiresPreAnalysisWarning"] is False
    asst_id = payload["assistantTurnId"]
    user_id = sent.json()["userTurnId"]

    # BackgroundTasks should complete quickly in tests; poll defensively.
    for _ in range(25):
        got = await client.get(f"/api/v1/chat-turns/{asst_id}")
        assert got.status_code == 200
        if got.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0)
    got2 = await client.get(f"/api/v1/chat-turns/{asst_id}")
    assert got2.json()["status"] == "COMPLETED"
    assert (got2.json()["contentMarkdown"] or "").strip()

    join_repo = ChatTurnSourceRepository(db_session)
    user_rows = await join_repo.list_for_turn(chat_turn_id=user_id)
    asst_rows = await join_repo.list_for_turn(chat_turn_id=UUID(asst_id))
    assert [r.source_id for r in asst_rows] == [r.source_id for r in user_rows]


@pytest.mark.asyncio
async def test_send_chat_message_with_valid_sources_attaches_sources_to_user_and_assistant(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "send2@example.com", "password": "password123"},
    )
    assert reg.status_code == 201
    me = await client.get("/api/v1/me")
    user_id = me.json()["id"]

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    chat_id = chat.json()["id"]

    src = Source(
        user_id=user_id,
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
        publisher="ExamplePub",
        author=None,
        published_at=None,
        extracted_text="X" * 1000,
        extracted_text_word_count=1000,
        extraction_confidence="HIGH",
        extraction_error=None,
        raw_text_retention="NOT_STORED",
        content_hash=None,
        metadata_={},
        source_complexity=None,
        segment_count=None,
        scan_status=None,
    )
    db_session.add(src)
    await db_session.commit()
    await db_session.refresh(src)

    sent = await client.post(
        f"/api/v1/chats/{chat_id}/turns",
        json={"content": "Use my source", "sourceIds": [str(src.id)]},
    )
    assert sent.status_code == 200
    payload = sent.json()
    assert payload["detectedInputType"] == "QUESTION"
    assert payload["detectedIntentType"] == "GENERAL_ASK"
    assert payload["createdSourceIds"] == []
    assert payload["requiresPreAnalysisWarning"] is False
    user_turn_id = payload["userTurnId"]
    asst_turn_id = payload["assistantTurnId"]

    join_repo = ChatTurnSourceRepository(db_session)
    user_rows = await join_repo.list_for_turn(chat_turn_id=user_turn_id)
    assert [r.source_id for r in user_rows] == [src.id]

    for _ in range(25):
        got = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
        if got.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0)

    asst_rows = await join_repo.list_for_turn(chat_turn_id=UUID(asst_turn_id))
    assert [r.source_id for r in asst_rows] == [src.id]


@pytest.mark.asyncio
async def test_send_with_source_from_other_user_returns_400_invalid_source_ref(client, db_session):
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "sendowner@example.com", "password": "password123"},
    )
    assert reg1.status_code == 201
    me1 = await client.get("/api/v1/me")
    user1 = me1.json()["id"]

    src = Source(
        user_id=user1,
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
        title="OwnerSource",
        publisher=None,
        author=None,
        published_at=None,
        extracted_text="hi",
        extracted_text_word_count=1,
        extraction_confidence="HIGH",
        extraction_error=None,
        raw_text_retention="NOT_STORED",
        content_hash=None,
        metadata_={},
        source_complexity=None,
        segment_count=None,
        scan_status=None,
    )
    db_session.add(src)
    await db_session.commit()
    await db_session.refresh(src)

    await client.post("/api/v1/auth/logout")

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "sendother@example.com", "password": "password123"},
    )
    assert reg2.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    chat_id = chat.json()["id"]

    sent = await client.post(
        f"/api/v1/chats/{chat_id}/turns",
        json={"content": "Try attach", "sourceIds": [str(src.id)]},
    )
    assert sent.status_code == 400
    assert sent.json()["errorCode"] == "INVALID_SOURCE_REF"


@pytest.mark.asyncio
async def test_send_on_archived_chat_returns_400_chat_archived(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "sendarch@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    chat_id = chat.json()["id"]

    archived = await client.patch(f"/api/v1/chats/{chat_id}", json={"status": "ARCHIVED"})
    assert archived.status_code == 200

    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Hello"})
    assert sent.status_code == 400
    assert sent.json()["errorCode"] == "CHAT_ARCHIVED"


@pytest.mark.asyncio
async def test_first_turn_auto_titles_chat_but_subsequent_turns_do_not_overwrite(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "sendtitle@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    created = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    chat_id = created.json()["id"]
    assert created.json()["title"] == "New chat"

    first_content = "A" * 80
    sent1 = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": first_content})
    assert sent1.status_code == 200
    p1 = sent1.json()
    assert p1["detectedInputType"] == "QUESTION"
    assert p1["detectedIntentType"] == "GENERAL_ASK"
    assert p1["createdSourceIds"] == []
    assert p1["requiresPreAnalysisWarning"] is False

    got1 = await client.get(f"/api/v1/chats/{chat_id}")
    assert got1.status_code == 200
    assert got1.json()["chat"]["title"] == first_content[:60]

    sent2 = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Second message"})
    assert sent2.status_code == 200
    p2 = sent2.json()
    assert p2["detectedInputType"] == "QUESTION"
    assert p2["detectedIntentType"] == "GENERAL_ASK"
    assert p2["createdSourceIds"] == []
    assert p2["requiresPreAnalysisWarning"] is False

    got2 = await client.get(f"/api/v1/chats/{chat_id}")
    assert got2.status_code == 200
    assert got2.json()["chat"]["title"] == first_content[:60]


@pytest.mark.asyncio
async def test_chat_last_turn_at_updated_on_send(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "sendlast@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    created = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    chat_id = created.json()["id"]

    before = await client.get(f"/api/v1/chats/{chat_id}")
    assert before.json()["chat"]["lastTurnAt"] is None

    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Hello"})
    assert sent.status_code == 200
    pl = sent.json()
    assert pl["detectedInputType"] == "QUESTION"
    assert pl["detectedIntentType"] == "GENERAL_ASK"
    assert pl["createdSourceIds"] == []
    assert pl["requiresPreAnalysisWarning"] is False

    after = await client.get(f"/api/v1/chats/{chat_id}")
    assert after.json()["chat"]["lastTurnAt"] is not None


@pytest.mark.asyncio
async def test_orphan_sweep_marks_old_running_assistant_turn_failed(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "orphansweep@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    me = await client.get("/api/v1/me")
    user_id = me.json()["id"]

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    chat_id = chat.json()["id"]

    # Create a running assistant turn older than cutoff.
    turn = ChatTurn(
        chat_id=UUID(chat_id),
        user_id=UUID(user_id),
        turn_index=0,
        role=ChatTurnRole.ASSISTANT.value,
        status=ChatTurnStatus.RUNNING.value,
        content_markdown=None,
        content_json=None,
        model_provider=None,
        model_name=None,
        updated_at=datetime.now(UTC) - timedelta(minutes=30),
    )
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)

    # Ensure updated_at is older than cutoff (use raw SQL to avoid ORM/onupdate behavior).
    old_ts = datetime.now(UTC) - timedelta(minutes=30)
    await db_session.execute(
        text("UPDATE chat_turns SET updated_at = :ts WHERE id = :id"),
        {"ts": old_ts, "id": turn.id},
    )
    await db_session.commit()
    await db_session.refresh(turn)
    assert turn.updated_at < datetime.now(UTC) - timedelta(minutes=10)

    await sweep_orphaned_turns_in_session(db=db_session)

    repo = ChatTurnRepository(db_session)
    refreshed = await repo.get_by_id(turn.id)
    assert refreshed is not None
    assert refreshed.status == ChatTurnStatus.FAILED.value
    assert refreshed.error_code == "RUN_ORPHANED"

