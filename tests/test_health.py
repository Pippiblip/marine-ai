"""Test the health endpoint."""

import pytest
from fastapi.testclient import TestClient

from orca.api.app import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health(client: TestClient):
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
