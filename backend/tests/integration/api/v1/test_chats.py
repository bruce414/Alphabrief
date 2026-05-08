import pytest


@pytest.mark.asyncio
async def test_create_chat_in_own_project_returns_201_for_catchall_and_real_project(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "chats1@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    projects = await client.get("/api/v1/projects")
    assert projects.status_code == 200
    catchall_id = projects.json()["items"][0]["id"]

    created1 = await client.post(f"/api/v1/projects/{catchall_id}/chats", json={})
    assert created1.status_code == 201
    assert created1.json()["projectId"] == catchall_id
    assert created1.json()["title"] == "New chat"
    assert created1.json()["status"] == "ACTIVE"

    p2 = await client.post("/api/v1/projects", json={"title": "My project", "kind": "THESIS"})
    assert p2.status_code == 201
    project_id = p2.json()["id"]

    created2 = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "Hello"})
    assert created2.status_code == 201
    assert created2.json()["projectId"] == project_id
    assert created2.json()["title"] == "Hello"


@pytest.mark.asyncio
async def test_create_chat_in_someone_elses_project_returns_403(client):
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "ownerchat@example.com", "password": "password123"},
    )
    assert reg1.status_code == 201

    p = await client.post("/api/v1/projects", json={"title": "Owner Project", "kind": "COVERAGE"})
    assert p.status_code == 201
    project_id = p.json()["id"]

    await client.post("/api/v1/auth/logout")

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "otherchat@example.com", "password": "password123"},
    )
    assert reg2.status_code == 201

    created = await client.post(f"/api/v1/projects/{project_id}/chats", json={})
    assert created.status_code == 403
    assert created.json()["errorCode"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_list_chats_archived_hidden_by_default_and_visible_with_include_archived(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "listarch@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    projects = await client.get("/api/v1/projects")
    project_id = projects.json()["items"][0]["id"]

    c1 = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "A"})
    c2 = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "B"})
    assert c1.status_code == 201
    assert c2.status_code == 201

    archived = await client.patch(f"/api/v1/chats/{c2.json()['id']}", json={"status": "ARCHIVED"})
    assert archived.status_code == 200
    assert archived.json()["status"] == "ARCHIVED"

    listed = await client.get(f"/api/v1/projects/{project_id}/chats")
    assert listed.status_code == 200
    titles = [i["title"] for i in listed.json()["items"]]
    assert "B" not in titles

    listed2 = await client.get(f"/api/v1/projects/{project_id}/chats?includeArchived=1")
    assert listed2.status_code == 200
    titles2 = [i["title"] for i in listed2.json()["items"]]
    assert "B" in titles2


@pytest.mark.asyncio
async def test_list_chats_pagination_round_trip_with_35_chats(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "paginate@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    for i in range(35):
        created = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": f"Chat {i}"})
        assert created.status_code == 201

    first = await client.get(f"/api/v1/projects/{project_id}/chats?limit=30")
    assert first.status_code == 200
    assert len(first.json()["items"]) == 30
    cursor = first.json()["nextCursor"]
    assert cursor is not None

    second = await client.get(f"/api/v1/projects/{project_id}/chats?limit=30&cursor={cursor}")
    assert second.status_code == 200
    assert len(second.json()["items"]) == 5
    assert second.json()["nextCursor"] is None


@pytest.mark.asyncio
async def test_patch_chat_archived_and_active(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "patchchat@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    created = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "X"})
    assert created.status_code == 201
    chat_id = created.json()["id"]

    a = await client.patch(f"/api/v1/chats/{chat_id}", json={"status": "ARCHIVED"})
    assert a.status_code == 200
    assert a.json()["status"] == "ARCHIVED"

    b = await client.patch(f"/api/v1/chats/{chat_id}", json={"status": "ACTIVE"})
    assert b.status_code == 200
    assert b.json()["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_delete_chat_returns_204(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "delchat@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    created = await client.post(f"/api/v1/projects/{project_id}/chats", json={"title": "X"})
    chat_id = created.json()["id"]

    deleted = await client.delete(f"/api/v1/chats/{chat_id}")
    assert deleted.status_code == 204

