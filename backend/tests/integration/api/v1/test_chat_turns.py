import pytest

from app.core.enums import ChatTurnRole, ChatTurnStatus
from app.models.chat_turn import ChatTurn
from app.models.source import Source
from app.repositories.chat_turn_repository import ChatTurnRepository
from app.repositories.chat_turn_source_repository import ChatTurnSourceRepository


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

