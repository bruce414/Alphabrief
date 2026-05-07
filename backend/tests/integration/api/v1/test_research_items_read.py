import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.research_item import ResearchItem
from app.repositories.research_item_repository import ResearchItemRepository


async def _register(client, email: str) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "displayName": "Test"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_research_items_unauthenticated_returns_401(client):
    resp = await client.get("/api/v1/research-items")
    assert resp.status_code == 401
    assert resp.json()["errorCode"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_research_item_nonexistent_returns_404(client):
    await _register(client, "ri404@example.com")
    missing = uuid.uuid4()
    resp = await client.get(f"/api/v1/research-items/{missing}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_research_item_other_user_returns_403(client, db_session):
    await _register(client, "ownercheck1@example.com")
    me = (await client.get("/api/v1/me")).json()
    owner_id = uuid.UUID(me["id"])

    await client.post("/api/v1/auth/logout")
    await _register(client, "ownercheck2@example.com")
    other = (await client.get("/api/v1/me")).json()
    other_id = uuid.UUID(other["id"])

    repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=other_id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="Other user's item",
        status="COMPLETED",
        original_user_input="q",
        analysis_mode="NOT_APPLICABLE",
        disclaimer="d",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await repo.add(item)
    await db_session.commit()

    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "ownercheck1@example.com", "password": "password123"},
    )
    me2 = (await client.get("/api/v1/me")).json()
    assert uuid.UUID(me2["id"]) == owner_id

    resp = await client.get(f"/api/v1/research-items/{item.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_owner_get_research_item_happy_path_returns_expected_shape(client, db_session):
    await _register(client, "rihappy@example.com")
    me = (await client.get("/api/v1/me")).json()
    user_id = uuid.UUID(me["id"])

    repo = ResearchItemRepository(db_session)
    item = ResearchItem(
        user_id=user_id,
        source_id=None,
        item_type="ASK_ANALYSIS",
        title="My item",
        status="COMPLETED",
        original_user_input="What is X?",
        output_markdown="Answer",
        output_json={"a": 1},
        short_summary="Short",
        confidence_label="HIGH",
        confidence_explanation=None,
        analysis_mode="NOT_APPLICABLE",
        disclaimer="Educational only.",
        model_provider=None,
        model_name=None,
        prompt_version=None,
        requested_research_mode=None,
        completion_strategy=None,
        coverage_mode=None,
        analysis_depth_summary={"sections": []},
        generated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await repo.add(item)
    await db_session.commit()

    resp = await client.get(f"/api/v1/research-items/{item.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(item.id)
    assert body["userId"] == str(user_id)
    assert body["itemType"] == "ASK_ANALYSIS"
    assert body["analysisMode"] == "NOT_APPLICABLE"
    assert "analysisDepthSummary" in body


@pytest.mark.asyncio
async def test_list_research_items_pagination_cursor_no_duplicates_and_order(client, db_session):
    await _register(client, "ripage@example.com")
    me = (await client.get("/api/v1/me")).json()
    user_id = uuid.UUID(me["id"])

    base = datetime(2026, 5, 7, 0, 0, 0, tzinfo=timezone.utc)
    repo = ResearchItemRepository(db_session)
    for i in range(25):
        item = ResearchItem(
            user_id=user_id,
            source_id=None,
            item_type="ASK_ANALYSIS",
            title=f"Item {i}",
            status="COMPLETED",
            original_user_input="q",
            analysis_mode="NOT_APPLICABLE",
            disclaimer="d",
            created_at=base + timedelta(seconds=i),
            updated_at=base + timedelta(seconds=i),
        )
        await repo.add(item)
    await db_session.commit()

    page1 = await client.get("/api/v1/research-items?limit=10")
    assert page1.status_code == 200
    b1 = page1.json()
    assert len(b1["items"]) == 10
    assert b1["nextCursor"] is not None

    page2 = await client.get(f"/api/v1/research-items?limit=10&cursor={b1['nextCursor']}")
    assert page2.status_code == 200
    b2 = page2.json()
    assert len(b2["items"]) == 10
    assert b2["nextCursor"] is not None

    page3 = await client.get(f"/api/v1/research-items?limit=10&cursor={b2['nextCursor']}")
    assert page3.status_code == 200
    b3 = page3.json()
    assert len(b3["items"]) == 5

    all_ids = [x["id"] for x in b1["items"]] + [x["id"] for x in b2["items"]] + [
        x["id"] for x in b3["items"]
    ]
    assert len(all_ids) == len(set(all_ids))

    all_created = [x["createdAt"] for x in b1["items"]] + [x["createdAt"] for x in b2["items"]] + [
        x["createdAt"] for x in b3["items"]
    ]
    assert all_created == sorted(all_created, reverse=True)

