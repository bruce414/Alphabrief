import pytest
from sqlalchemy import delete

from app.models.project import Project


@pytest.mark.asyncio
async def test_new_user_get_projects_returns_exactly_one_catchall(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "p1@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["kind"] == "CATCHALL"


@pytest.mark.asyncio
async def test_post_project_kind_coverage_returns_201(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "p2@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    created = await client.post(
        "/api/v1/projects",
        json={"title": "My coverage project", "kind": "COVERAGE"},
    )
    assert created.status_code == 201
    assert created.json()["kind"] == "COVERAGE"


@pytest.mark.asyncio
async def test_post_project_kind_catchall_returns_400_invalid_project_kind(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "p3@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    created = await client.post(
        "/api/v1/projects",
        json={"title": "nope", "kind": "CATCHALL"},
    )
    assert created.status_code == 400
    assert created.json()["errorCode"] == "INVALID_PROJECT_KIND"


@pytest.mark.asyncio
async def test_patch_catchall_returns_400_immutable_catchall(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "p4@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    items = (await client.get("/api/v1/projects")).json()["items"]
    catchall_id = items[0]["id"]

    patched = await client.patch(f"/api/v1/projects/{catchall_id}", json={"title": "rename"})
    assert patched.status_code == 400
    assert patched.json()["errorCode"] == "IMMUTABLE_CATCHALL"


@pytest.mark.asyncio
async def test_delete_catchall_returns_400_immutable_catchall(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "p5@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    items = (await client.get("/api/v1/projects")).json()["items"]
    catchall_id = items[0]["id"]

    deleted = await client.delete(f"/api/v1/projects/{catchall_id}")
    assert deleted.status_code == 400
    assert deleted.json()["errorCode"] == "IMMUTABLE_CATCHALL"


@pytest.mark.asyncio
async def test_cross_user_get_patch_delete_returns_403(client):
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "owner@example.com", "password": "password123"},
    )
    assert reg1.status_code == 201

    created = await client.post(
        "/api/v1/projects",
        json={"title": "Owner Project", "kind": "THESIS"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    await client.post("/api/v1/auth/logout")

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "password123"},
    )
    assert reg2.status_code == 201

    g = await client.get(f"/api/v1/projects/{project_id}")
    assert g.status_code == 403
    p = await client.patch(f"/api/v1/projects/{project_id}", json={"title": "hack"})
    assert p.status_code == 403
    d = await client.delete(f"/api/v1/projects/{project_id}")
    assert d.status_code == 403


@pytest.mark.asyncio
async def test_lazy_catchall_recreated_if_missing(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "lazy@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    first = await client.get("/api/v1/projects")
    assert first.status_code == 200
    catchall_id = first.json()["items"][0]["id"]

    await db_session.execute(delete(Project).where(Project.id == catchall_id))
    await db_session.commit()

    second = await client.get("/api/v1/projects")
    assert second.status_code == 200
    items = second.json()["items"]
    assert len(items) >= 1
    assert items[0]["kind"] == "CATCHALL"

