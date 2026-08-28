"""Smoke tests for the minimal web UI."""

from fastapi.testclient import TestClient

from orca.api.app import app


def test_home_page_renders():
    """The root page should render the ORCA fixture test console."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "ORCA" in response.text
    assert "Run all checks" in response.text
    assert "/api/tools/imd_get_marine_warnings" in response.text


def test_tool_api_exposes_fixture_response():
    """The browser API should expose a sourced, timestamped tool response."""
    client = TestClient(app)
    response = client.get("/api/tools/imd_get_marine_warnings?cell_id=calm")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["source"] == "imd_marine"
    assert body["payload"]["wave_height"]["unit"] == "m"
    assert body["retrieved_at"]


def test_tool_api_exposes_empty_and_error_states():
    """The console should make missing and failed sources visible."""
    client = TestClient(app)
    empty = client.get("/api/tools/incois_get_pfz?cell_id=missing-cell")
    failed = client.get("/api/tools/isro_get_chlorophyll?force_error=true")
    assert empty.json()["status"] == "empty"
    assert failed.json()["status"] == "error"
    assert failed.json()["error"] == "forced_error"


def test_unknown_tool_returns_not_found():
    """The API should reject tool names that are not part of the registry."""
    response = TestClient(app).get("/api/tools/not-a-tool")
    assert response.status_code == 404
