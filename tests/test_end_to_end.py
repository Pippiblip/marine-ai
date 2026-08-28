"""Acceptance tests for the complete ORCA graph path."""

from orca.graph import run_query
from orca.guardrails.provenance import verify
from orca.guardrails.thresholds import WAVE_UNSAFE_M
from orca.schemas import Measurement, Severity, SourceName


def _all_measurements(state) -> list[Measurement]:
    values: list[Measurement] = []
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
    if geo and geo.bearing_deg is not None:
        values.append(
            Measurement(
                value=geo.bearing_deg,
                unit="deg",
                source=SourceName.INCOIS_PFZ,
                retrieved_at=geo.distance_km.retrieved_at if geo.distance_km else marine.pfz_nodes[0].depth.retrieved_at,
            )
        )
    return values


def test_pfz_nearest_returns_sourced_answer():
    """A PFZ query should traverse specialists and cite retrieved facts."""
    state = run_query("Where is the nearest fishing zone?", cell_id="calm")
    text = state["final_response_text"]
    assert state["intent"] == "pfz_nearest"
    assert state["guardrail_status"] == "ok"
    assert "nearest fishing zone" in text
    assert "km" in text
    assert state["citations"]
    assert "INCOIS" in text or "incois" in " ".join(state["citations"]).lower()
    extra = {f"{WAVE_UNSAFE_M:g}", f"{WAVE_UNSAFE_M:.1f}"}
    ok, offenders = verify(text, _all_measurements(state), extra_allowed=extra)
    assert ok, offenders


def test_safety_unsafe():
    """Cyclone cell must force a no-go the model cannot soften."""
    state = run_query("Is it safe to go out tomorrow morning?", cell_id="cyclone")
    text = state["final_response_text"]
    assert state["intent"] == "safety_check"
    assert any(flag.severity == Severity.DANGER for flag in state["safety_flags"])
    assert "Do not go out" in text
    assert "3.4" in text
    assert "safe" not in text.lower() or "Do not go out" in text


def test_source_down():
    """Killing the weather tool must speak the explicit-failure template."""
    run_query("Is it safe to go out tomorrow morning?", cell_id="cyclone")
    state = run_query(
        "Is it safe to go out tomorrow morning?",
        cell_id="cyclone",
        force_error_sources=["imd_marine"],
    )
    text = state["final_response_text"]
    assert state["guardrail_status"] == "failed"
    assert "won't guess" in text
    assert "3.4" in text
    assert "12.5" not in text


def test_missing_location_is_explicit():
    """Location-dependent requests must ask for location rather than guess."""
    state = run_query("Where is the nearest fishing zone?", user_location=None)
    assert "need your location" in state["final_response_text"]
