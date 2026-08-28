"""Synthesis obeys the guardrail gate and never invents numbers."""

from datetime import datetime, timezone

from orca.agents.synthesis import synthesis_node
from orca.schemas import Measurement, SafetyFlag, Severity, SourceName


def test_danger_flag_forces_nogo_template():
    """A DANGER flag must produce the no-go template with the tripped number."""
    wave = Measurement(
        value=3.4,
        unit="m",
        source=SourceName.IMD_MARINE,
        retrieved_at=datetime.now(timezone.utc),
    )
    out = synthesis_node(
        {
            "guardrail_status": "ok",
            "safety_flags": [
                SafetyFlag(
                    code="high_wave",
                    severity=Severity.DANGER,
                    message_key="danger_high_wave",
                    triggered_by=[wave],
                    threshold_repr="wave_height > 2.5 m",
                )
            ],
            "user_location": None,
            "intent": "safety_check",
            "source_lang": "en-IN",
        }
    )
    assert "Do not go out" in out["final_response_text"]
    assert "3.4" in out["final_response_text"]


def test_failed_status_uses_unavailable_template():
    """Failed guardrail status must not produce a normal answer."""
    out = synthesis_node(
        {
            "guardrail_status": "failed",
            "safety_flags": [],
            "source_lang": "en-IN",
        }
    )
    assert "won't guess" in out["final_response_text"]


def test_location_unknown_when_missing_gps():
    """Missing location asks rather than guessing coordinates."""
    out = synthesis_node(
        {
            "guardrail_status": "ok",
            "safety_flags": [],
            "intent": "pfz_nearest",
            "user_location": None,
            "source_lang": "en-IN",
        }
    )
    assert "need your location" in out["final_response_text"]
