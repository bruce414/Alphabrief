import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """HTTP client against the FastAPI app.

    Tests exercise real routes and use ``DATABASE_URL`` from ``backend/.env``
    (via ``app.core.config``). Prefer adding a dedicated test DB fixture later;
    for now Postgres must be running and migrations applied.
    """
    with TestClient(app) as test_client:
        yield test_client
