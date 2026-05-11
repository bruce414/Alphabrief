"""Integration tests for GET /projects/{id}/canvas (lazy Canvas creation)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_get_canvas_lazy_creates_and_returns_stable_id(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "canvas-gc1@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    first = await client.get(f"/api/v1/projects/{project_id}/canvas")
    assert first.status_code == 200
    body1 = first.json()
    assert body1["projectId"] == project_id
    canvas_id = body1["id"]

    second = await client.get(f"/api/v1/projects/{project_id}/canvas")
    assert second.status_code == 200
    assert second.json()["id"] == canvas_id


@pytest.mark.asyncio
async def test_get_canvas_other_users_project_returns_403(client):
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "canvas-own@example.com", "password": "password123"},
    )
    assert reg1.status_code == 201
    owner_project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]

    await client.post("/api/v1/auth/logout")

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "canvas-other@example.com", "password": "password123"},
    )
    assert reg2.status_code == 201

    denied = await client.get(f"/api/v1/projects/{owner_project_id}/canvas")
    assert denied.status_code == 403
    assert denied.json()["errorCode"] == "FORBIDDEN"
