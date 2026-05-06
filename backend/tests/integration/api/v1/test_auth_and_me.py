import pytest


@pytest.mark.asyncio
async def test_register_login_me_logout_flow(client):
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "password123", "displayName": "Alex"},
    )
    assert register.status_code == 201
    assert register.json()["email"] == "user@example.com"
    assert "set-cookie" in register.headers

    me = await client.get("/api/v1/me")
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "user@example.com"
    assert body["displayName"] == "Alex"

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 204

    me2 = await client.get("/api/v1/me")
    assert me2.status_code == 401
    assert me2.json()["errorCode"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_duplicate_email_registration_returns_400_invalid_input(client):
    first = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    assert second.status_code == 400
    assert second.json()["errorCode"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "pw@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    await client.post("/api/v1/auth/logout")

    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "pw@example.com", "password": "wrong-password"},
    )
    assert bad.status_code == 401
    assert bad.json()["errorCode"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_me_unauthenticated_returns_401(client):
    response = await client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["errorCode"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_register_short_password_returns_400_invalid_input(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert response.status_code == 400
    assert response.json()["errorCode"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_patch_me_updates_display_name(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "patchme@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    updated = await client.patch("/api/v1/me", json={"displayName": "New Name"})
    assert updated.status_code == 200
    assert updated.json()["displayName"] == "New Name"

