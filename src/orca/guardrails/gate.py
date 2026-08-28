"""Deterministic gate that runs after specialists and before synthesis."""

from __future__ import annotations

from datetime import datetime, timezone

from orca.guardrails.freshness import PFZ_MAX_AGE_S, SAFETY_MAX_AGE_S, is_fresh
from orca.schemas import SourceName
from orca.state import PlatformState


def guardrail_node(state: PlatformState) -> dict:
    """Apply freshness and missing-source gates. Never invents flags or numbers."""
    notes: list[str] = []
    now = datetime.now(timezone.utc)
    freshness = state.get("data_freshness") or {}
    sources = {s.value if isinstance(s, SourceName) else str(s) for s in freshness}
    subtasks = state.get("subtasks") or []
    intent = state.get("intent")
    status: str = "ok"

    weather_required = "weather_risk" in subtasks and intent == "safety_check"
    marine_required = "marine_data" in subtasks

    if weather_required and SourceName.IMD_MARINE.value not in sources:
        status = "failed"
        notes.append("imd_marine unavailable")
    if marine_required and SourceName.INCOIS_PFZ.value not in sources:
        status = "failed"
        notes.append("incois_pfz unavailable")

    weather = state.get("weather_risk_result")
    if status == "ok" and weather_required and weather:
        readings = [
            m
            for m in (weather.wave_height, weather.wind_speed, weather.cyclone_distance)
            if m is not None
        ]
        if readings and any(
            not is_fresh(reading, max_age_s=SAFETY_MAX_AGE_S, now=now) for reading in readings
        ):
            status = "stale"
            notes.append("marine warning reading is stale")

    marine = state.get("marine_data_result")
    if status == "ok" and marine and marine.pfz_nodes:
        depths = [node.depth for node in marine.pfz_nodes if node.depth]
        if depths and any(not is_fresh(d, max_age_s=PFZ_MAX_AGE_S, now=now) for d in depths):
            status = "stale"
            notes.append("PFZ advisory is stale")

    return {"guardrail_status": status, "guardrail_notes": notes}
