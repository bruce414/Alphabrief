"""Integration tests for Canvas connection endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_post_connection_between_elements_same_canvas(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "conn-ok@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    canvas_id = (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]

    a = await client.post(
        f"/api/v1/canvases/{canvas_id}/elements",
        json={
            "elementType": "TEXT",
            "contentMarkdown": "a",
            "contentJson": {},
            "x": 0.0,
            "y": 0.0,
            "provenanceKind": "MANUAL",
        },
    )
    b = await client.post(
        f"/api/v1/canvases/{canvas_id}/elements",
        json={
            "elementType": "TEXT",
            "contentMarkdown": "b",
            "contentJson": {},
            "x": 50.0,
            "y": 50.0,
            "provenanceKind": "MANUAL",
        },
    )
    assert a.status_code == 201 and b.status_code == 201
    aid, bid = a.json()["id"], b.json()["id"]

    conn = await client.post(
        f"/api/v1/canvases/{canvas_id}/connections",
        json={
            "fromElementId": aid,
            "toElementId": bid,
            "label": "supports",
            "connectionType": "SUPPORTS",
            "styleJson": {},
        },
    )
    assert conn.status_code == 201
    payload = conn.json()
    assert payload["fromElementId"] == aid
    assert payload["toElementId"] == bid
    assert payload["connectionType"] == "SUPPORTS"

    listed = await client.get(f"/api/v1/canvases/{canvas_id}/connections")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1


@pytest.mark.asyncio
async def test_post_connection_rejects_cross_canvas_elements(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "conn-xc@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    p1 = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    p2_resp = await client.post("/api/v1/projects", json={"title": "Second", "kind": "COVERAGE"})
    assert p2_resp.status_code == 201
    p2 = p2_resp.json()["id"]

    c1 = (await client.get(f"/api/v1/projects/{p1}/canvas")).json()["id"]
    c2 = (await client.get(f"/api/v1/projects/{p2}/canvas")).json()["id"]

    el1 = await client.post(
        f"/api/v1/canvases/{c1}/elements",
        json={
            "elementType": "TEXT",
            "contentMarkdown": "on canvas 1",
            "contentJson": {},
            "x": 0.0,
            "y": 0.0,
            "provenanceKind": "MANUAL",
        },
    )
    el2 = await client.post(
        f"/api/v1/canvases/{c2}/elements",
        json={
            "elementType": "TEXT",
            "contentMarkdown": "on canvas 2",
            "contentJson": {},
            "x": 0.0,
            "y": 0.0,
            "provenanceKind": "MANUAL",
        },
    )
    assert el1.status_code == 201 and el2.status_code == 201

    bad = await client.post(
        f"/api/v1/canvases/{c1}/connections",
        json={
            "fromElementId": el1.json()["id"],
            "toElementId": el2.json()["id"],
            "connectionType": "RELATED_TO",
        },
    )
    assert bad.status_code == 400
    assert bad.json()["errorCode"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_patch_and_delete_connection(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "conn-patch@example.com", "password": "password123"},
    )
    assert reg.status_code == 201

    project_id = (await client.get("/api/v1/projects")).json()["items"][0]["id"]
    canvas_id = (await client.get(f"/api/v1/projects/{project_id}/canvas")).json()["id"]

    el = []
    for _ in range(2):
        r = await client.post(
            f"/api/v1/canvases/{canvas_id}/elements",
            json={
                "elementType": "TEXT",
                "contentMarkdown": "x",
                "contentJson": {},
                "x": 0.0,
                "y": 0.0,
                "provenanceKind": "MANUAL",
            },
        )
        assert r.status_code == 201
        el.append(r.json()["id"])

    created = await client.post(
        f"/api/v1/canvases/{canvas_id}/connections",
        json={
            "fromElementId": el[0],
            "toElementId": el[1],
            "label": "before",
            "connectionType": "SUPPORTS",
            "styleJson": {"a": 1},
        },
    )
    assert created.status_code == 201
    cid = created.json()["id"]

    patched = await client.patch(
        f"/api/v1/canvas-connections/{cid}",
        json={
            "label": "after",
            "connectionType": "DEPENDS_ON",
            "styleJson": {"b": 2},
        },
    )
    assert patched.status_code == 200
    assert patched.json()["label"] == "after"
    assert patched.json()["connectionType"] == "DEPENDS_ON"
    assert patched.json()["styleJson"] == {"b": 2}

    deleted = await client.delete(f"/api/v1/canvas-connections/{cid}")
    assert deleted.status_code == 204

    listed = await client.get(f"/api/v1/canvases/{canvas_id}/connections")
    assert listed.json()["items"] == []
