"""Brief API tests.

These calls hit the real SQLAlchemy engine from ``DATABASE_URL``. Later, swap in a
transaction-scoped test database fixture so tests stay isolated and Postgres is optional.
"""

import uuid


def test_post_brief_with_valid_source_url_creates(client):
    response = client.post(
        "/api/v1/briefs",
        json={"source_url": "https://example.com/article"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["brief_type"] == "BASIC"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source_url"] == "https://example.com/article"


def test_get_brief_returns_created_brief(client):
    created = client.post(
        "/api/v1/briefs",
        json={
            "source_url": "https://example.org/page",
            "title": "My title",
            "brief_type": "BASIC",
        },
    )
    assert created.status_code == 201
    brief_id = created.json()["id"]

    response = client.get(f"/api/v1/briefs/{brief_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == brief_id
    assert data["title"] == "My title"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source_type"] == "URL"


def test_get_brief_unknown_id_returns_404(client):
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/briefs/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Brief not found"
