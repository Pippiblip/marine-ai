"""Smoke tests for the web client and query API."""

from fastapi.testclient import TestClient

from orca.api.app import app


def test_home_page_renders():
    """The root page should render the ORCA push-to-talk client."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "ORCA" in response.text
    assert "Fixture mode" in response.text
    assert "Four-minute judge path" in response.text
    assert "/api/query" in response.text


def test_query_api_returns_sourced_answer():
    """The browser query API should return a sourced fishing-zone answer."""
    client = TestClient(app)
    response = client.post(
        "/api/query",
        json={"text": "Where is the nearest fishing zone?", "cell_id": "calm"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["intent"] == "pfz_nearest"
    assert body["guardrail_status"] == "ok"
    assert "fishing zone" in body["text"].lower()
    assert body["citations"]
    assert body["data_mode"] == "mock"
    assert "channel_gateway" in body["path"]
    assert body["readings"]


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
