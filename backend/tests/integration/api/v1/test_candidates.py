import asyncio
from uuid import UUID

import pytest

from app.clients.ai_provider_client import MockAiProviderClient
from app.models.source import Source


@pytest.mark.asyncio
async def test_candidates_created_after_assistant_completed_and_listed(client, db_session, monkeypatch):
    # Force assistant reply to contain two "###" headers so mock candidate extraction returns 2.
    async def _mock_reply(self, prompt):  # type: ignore[no-untyped-def]
        content = "### One\n\nA\n\n### Two\n\nB\n\n" + ("x" * 50)
        return {"content_markdown": content, "content_json": {}, "input_tokens": 1, "output_tokens": 1}

    monkeypatch.setattr(MockAiProviderClient, "generate_chat_reply", _mock_reply)

    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cand1@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "T"})
    chat_id = chat.json()["id"]

    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Hello"})
    assert sent.status_code == 200
    asst_turn_id = sent.json()["assistantTurnId"]

    # Poll assistant turn to COMPLETED.
    for _ in range(50):
        got = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
        assert got.status_code == 200
        if got.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0)
    got2 = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
    assert got2.json()["status"] == "COMPLETED"
    assert (got2.json()["contentMarkdown"] or "").strip()

    # Poll candidates (best-effort background task) up to 5s.
    deadline = asyncio.get_event_loop().time() + 5.0
    items = []
    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(f"/api/v1/chat-turns/{asst_turn_id}/candidates")
        assert resp.status_code == 200
        items = resp.json()["items"]
        if len(items) == 2:
            break
        await asyncio.sleep(0.05)

    assert len(items) == 2
    assert all(i["status"] == "PENDING" for i in items)


@pytest.mark.asyncio
async def test_promote_dismiss_and_idempotency(client, monkeypatch):
    async def _mock_reply(self, prompt):  # type: ignore[no-untyped-def]
        content = "### PromoteMe\n\nBody\n\n### KeepMe\n\nBody\n\n"
        return {"content_markdown": content, "content_json": {}, "input_tokens": 1, "output_tokens": 1}

    monkeypatch.setattr(MockAiProviderClient, "generate_chat_reply", _mock_reply)

    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cand2@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "T"})
    chat_id = chat.json()["id"]

    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Hello"})
    asst_turn_id = sent.json()["assistantTurnId"]

    for _ in range(50):
        got = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
        if got.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0)

    # Wait for candidates to show up.
    deadline = asyncio.get_event_loop().time() + 5.0
    items = []
    while asyncio.get_event_loop().time() < deadline:
        items = (await client.get(f"/api/v1/chat-turns/{asst_turn_id}/candidates")).json()["items"]
        if len(items) == 2:
            break
        await asyncio.sleep(0.05)
    assert len(items) == 2

    cand_id = items[0]["id"]
    promoted = await client.post(f"/api/v1/candidates/{cand_id}/promote", json={})
    assert promoted.status_code == 200
    block = promoted.json()
    assert block["provenanceKind"] == "CHAT_TURN"
    assert block["provenanceChatTurnId"] == asst_turn_id
    assert (block["contentMarkdown"] or "").strip()

    # Promoting again returns same block id (idempotent).
    promoted2 = await client.post(f"/api/v1/candidates/{cand_id}/promote", json={})
    assert promoted2.status_code == 200
    assert promoted2.json()["id"] == block["id"]

    # Dismiss other candidate.
    other_id = items[1]["id"]
    dismissed = await client.post(f"/api/v1/candidates/{other_id}/dismiss", json={})
    assert dismissed.status_code == 200

    # Promote dismissed -> 400 CANDIDATE_DISMISSED.
    bad = await client.post(f"/api/v1/candidates/{other_id}/promote", json={})
    assert bad.status_code == 400
    assert bad.json()["errorCode"] == "CANDIDATE_DISMISSED"


@pytest.mark.asyncio
async def test_candidate_extraction_failure_does_not_fail_assistant_turn(client, monkeypatch):
    # Keep chat reply non-empty, but make extract_candidates raise.
    async def _mock_reply(self, prompt):  # type: ignore[no-untyped-def]
        content = "### Header\n\nThis is fine.\n\n"
        return {"content_markdown": content, "content_json": {}, "input_tokens": 1, "output_tokens": 1}

    async def _raise(self, *, user_message, assistant_reply, attached_sources):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")

    monkeypatch.setattr(MockAiProviderClient, "generate_chat_reply", _mock_reply)
    monkeypatch.setattr(MockAiProviderClient, "extract_candidates", _raise)

    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cand3@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "T"})
    chat_id = chat.json()["id"]

    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Hello"})
    assert sent.status_code == 200
    asst_turn_id = sent.json()["assistantTurnId"]

    # Poll assistant turn to COMPLETED; should succeed even though extraction fails.
    for _ in range(50):
        got = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
        assert got.status_code == 200
        if got.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0)
    got2 = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
    assert got2.json()["status"] == "COMPLETED"
    assert (got2.json()["contentMarkdown"] or "").strip()

    # Candidates should remain empty (best effort).
    resp = await client.get(f"/api/v1/chat-turns/{asst_turn_id}/candidates")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_cross_user_cannot_promote_candidate_returns_403(client, monkeypatch):
    async def _mock_reply(self, prompt):  # type: ignore[no-untyped-def]
        content = "### X\n\nBody\n\n"
        return {"content_markdown": content, "content_json": {}, "input_tokens": 1, "output_tokens": 1}

    monkeypatch.setattr(MockAiProviderClient, "generate_chat_reply", _mock_reply)

    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "cand4-owner@example.com", "password": "password123"},
    )
    assert reg1.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    chat = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "T"})
    chat_id = chat.json()["id"]

    sent = await client.post(f"/api/v1/chats/{chat_id}/turns", json={"content": "Hello"})
    asst_turn_id = sent.json()["assistantTurnId"]

    for _ in range(50):
        got = await client.get(f"/api/v1/chat-turns/{asst_turn_id}")
        if got.json()["status"] == "COMPLETED":
            break
        await asyncio.sleep(0)

    # Wait for candidate.
    deadline = asyncio.get_event_loop().time() + 5.0
    items = []
    while asyncio.get_event_loop().time() < deadline:
        items = (await client.get(f"/api/v1/chat-turns/{asst_turn_id}/candidates")).json()["items"]
        if len(items) == 1:
            break
        await asyncio.sleep(0.05)
    assert len(items) == 1
    cand_id = items[0]["id"]

    await client.post("/api/v1/auth/logout")

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "cand4-other@example.com", "password": "password123"},
    )
    assert reg2.status_code == 201

    denied = await client.post(f"/api/v1/candidates/{cand_id}/promote", json={})
    assert denied.status_code == 403
    assert denied.json()["errorCode"] == "FORBIDDEN"

