"""Acceptance tests for the complete ORCA graph path."""

from orca.graph import run_query
from orca.guardrails.provenance import verify
from orca.schemas import Severity, SourceName
from orca.tools.imd import MarineWarningPayload


def _all_measurements(state):
    values = []
    marine = state.get("marine_data_result")
    weather = state.get("weather_risk_result")
    geo = state.get("geospatial_result")
    if marine:
        values.extend(m for m in (marine.chlorophyll, marine.sst) if m)
        for node in marine.pfz_nodes:
            if node.depth:
                values.append(node.depth)
    if weather:
        values.extend(
            m
            for m in (
                weather.wave_height,
                weather.wind_speed,
                weather.cyclone_distance,
                weather.swell_surge,
            )
            if m
        )
    if geo and geo.distance_km:
        values.append(geo.distance_km)
    return values


def test_pfz_nearest_returns_sourced_answer():
    """A PFZ query should traverse specialists and cite retrieved facts."""
    state = run_query("Where is the nearest fishing zone?", cell_id="calm")
    assert state["intent"] == "pfz_nearest"
    assert state["guardrail_status"] == "ok"
    text = state["final_response_text"]
    assert "nearest fishing zone" in text
    assert "Source:" in text
    assert "INCOIS" in text
    assert state["citations"]
    geo = state["geospatial_result"]
    assert geo.nearest_pfz is not None
    assert geo.distance_km is not None
    assert f"{geo.distance_km.value:.1f}" in text
    ok, offenders = verify(text, _all_measurements(state), extra_allowed={"2.5", "25", "300", "2"})
    assert ok, offenders


def test_safety_unsafe():
    """Cyclone-cell safety query must be a hard no-go the model cannot soften."""
    state = run_query("Is it safe to go out tomorrow morning?", cell_id="cyclone")
    assert state["intent"] == "safety_check"
    assert state["guardrail_status"] == "ok"
    flags = state["safety_flags"]
    assert any(flag.severity == Severity.DANGER for flag in flags)
    text = state["final_response_text"]
    assert "Do not go out" in text
    assert "3.4" in text
    assert "safe" not in text.lower() or "Do not" in text
    assert "2.5" in text


def test_source_down():
    """A failed weather source must speak the explicit-failure template."""
    warm = run_query("Is it safe to go out tomorrow morning?", cell_id="cyclone")
    assert warm["weather_risk_result"].wave_height is not None
    state = run_query(
        "Is it safe to go out tomorrow morning?",
        cell_id="cyclone",
        force_error_sources=["imd_marine"],
    )
    assert state["guardrail_status"] == "failed"
    text = state["final_response_text"]
    assert "won't guess" in text
    assert "3.4" in text
    last = warm["weather_risk_result"].wave_height
    assert last is not None
    assert f"{last.value:g}" in text


def test_missing_location_is_explicit():
    """Location-dependent requests must ask for location rather than guess."""
    state = run_query("Where is the nearest fishing zone?", user_location=None)
    assert "need your location" in state["final_response_text"]
