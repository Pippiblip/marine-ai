"""Tests for mock-first tools and the data adapter layer."""

from datetime import datetime, timezone

from orca.schemas import Measurement, SourceName
from orca.tools.base import get_tool
from orca.tools.imd import MarineWarningRequest
from orca.tools.incois import PFZRequest
from orca.tools.isro import ChlorophyllRequest


def test_incois_pfz_mock_ok():
    """The PFZ tool should return valid PFZ data for a known cell."""
    tool = get_tool("incois_get_pfz")
    response = tool(PFZRequest(cell_id="calm", date=datetime.now(timezone.utc)))
    assert response.status.value == "ok"
    assert response.payload is not None
    assert len(response.payload.nodes) > 0
    assert isinstance(response.payload.nodes[0].depth, Measurement)


def test_incois_pfz_unknown_cell_is_empty():
    """Unknown cells should produce an EMPTY response rather than crashing."""
    tool = get_tool("incois_get_pfz")
    response = tool(PFZRequest(cell_id="missing-cell"))
    assert response.status.value == "empty"


def test_imd_weather_mock_ok():
    """Marine warnings should return wind and wave readings for known cells."""
    tool = get_tool("imd_get_marine_warnings")
    response = tool(MarineWarningRequest(cell_id="calm"))
    assert response.status.value == "ok"
    assert response.payload is not None
    assert response.payload.wind_speed.unit == "kt"
    assert response.payload.wave_height.unit == "m"


def test_isro_chlorophyll_mock_ok():
    """Satellite EO data should return chlorophyll and SST for known cells."""
    tool = get_tool("isro_get_chlorophyll")
    response = tool(ChlorophyllRequest(cell_id="calm"))
    assert response.status.value == "ok"
    assert response.payload is not None
    assert response.payload.chlorophyll.unit == "mg_m3"
    assert response.payload.sst.unit == "deg_c"


def test_force_error_returns_error_response():
    """The mock tool should surface an explicit ERROR when forced."""
    tool = get_tool("imd_get_marine_warnings")
    response = tool(MarineWarningRequest(cell_id="calm", force_error=True))
    assert response.status.value == "error"
    assert response.error is not None


def test_tool_registry_contains_expected_tools():
    """Expected tools should be registered for the mock-first MVP."""
    assert get_tool("incois_get_pfz").source == SourceName.INCOIS_PFZ
    assert get_tool("imd_get_marine_warnings").source == SourceName.IMD_MARINE
    assert get_tool("isro_get_chlorophyll").source == SourceName.ISRO_CHLOROPHYLL
