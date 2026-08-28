"""Serialize graph state into a judge-friendly API payload."""

from __future__ import annotations

from typing import Any, Optional

from orca.config import settings
from orca.schemas import Measurement, SafetyFlag
from orca.state import PlatformState


def _reading(label: str, measurement: Optional[Measurement]) -> Optional[dict[str, Any]]:
    if measurement is None:
        return None
    return {
        "label": label,
        "value": measurement.value,
        "unit": measurement.unit,
        "source": measurement.source.value,
        "retrieved_at": measurement.retrieved_at.isoformat(),
    }


def _flag(flag: SafetyFlag) -> dict[str, Any]:
    trigger = flag.triggered_by[0] if flag.triggered_by else None
    return {
        "code": flag.code,
        "severity": flag.severity.value,
        "rule": flag.threshold_repr,
        "value": trigger.value if trigger else None,
        "unit": trigger.unit if trigger else None,
    }


def query_view(state: PlatformState) -> dict[str, Any]:
    """Fields the web demo needs: path, flags, sourced readings, mode."""
    weather = state.get("weather_risk_result")
    marine = state.get("marine_data_result")
    geo = state.get("geospatial_result")
    readings = [
        item
        for item in (
            _reading("wave_height", weather.wave_height if weather else None),
            _reading("wind_speed", weather.wind_speed if weather else None),
            _reading("cyclone_distance", weather.cyclone_distance if weather else None),
            _reading("distance_to_zone", geo.distance_km if geo else None),
            _reading("chlorophyll", marine.chlorophyll if marine else None),
        )
        if item is not None
    ]
    subtasks = list(state.get("subtasks") or [])
    path = ["channel_gateway", "router", *subtasks, "guardrail", "synthesis"]
    return {
        "data_mode": settings.data_mode,
        "llm_provider": settings.llm_provider,
        "speech_provider": settings.speech_provider,
        "cell_id": state.get("cell_id"),
        "path": path,
        "subtasks": subtasks,
        "guardrail_notes": list(state.get("guardrail_notes") or []),
        "safety_flags": [_flag(f) for f in (state.get("safety_flags") or [])],
        "readings": readings,
    }
