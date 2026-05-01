def test_root_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_api_v1_health_returns_200(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
