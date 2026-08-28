"""Weather retrieval and deterministic safety evaluation."""

from __future__ import annotations

from orca.agents.common import cell_id, force_error_for
from orca.guardrails.resilience import fetch
from orca.guardrails.thresholds import evaluate
from orca.logging import get_logger
from orca.schemas import SourceName, WeatherRiskResult
from orca.state import PlatformState
from orca.tools.base import get_tool
from orca.tools.imd import MarineWarningPayload, MarineWarningRequest
from orca.tools.incois import OceanStatePayload, OceanStateRequest

logger = get_logger(__name__)


def weather_risk_node(state: PlatformState) -> dict:
    """Fetch marine warnings and append only threshold-derived safety flags."""
    # SAFETY: this node is the only writer of safety_flags.
    freshness = dict(state.get("data_freshness") or {})
    cid = cell_id(state)
    response = fetch(
        get_tool("imd_get_marine_warnings"),
        MarineWarningRequest(
            cell_id=cid,
            force_error=force_error_for(state, SourceName.IMD_MARINE),
        ),
        SourceName.IMD_MARINE,
        freshness_dict=freshness,
    )
    ocean = fetch(
        get_tool("incois_get_ocean_state"),
        OceanStateRequest(
            cell_id=cid,
            force_error=force_error_for(state, SourceName.INCOIS_OCEAN_STATE),
        ),
        SourceName.INCOIS_OCEAN_STATE,
        freshness_dict=freshness,
    )
    payload = response.payload if isinstance(response.payload, MarineWarningPayload) else None
    ocean_payload = ocean.payload if isinstance(ocean.payload, OceanStatePayload) else None
    swell = None
    if payload and payload.swell_surge:
        swell = payload.swell_surge
    elif ocean_payload:
        swell = ocean_payload.swell_surge
    result = WeatherRiskResult(
        wave_height=payload.wave_height if payload else None,
        wind_speed=payload.wind_speed if payload else None,
        cyclone_distance=payload.cyclone_distance if payload else None,
        swell_surge=swell,
        source_freshness={
            source: retrieved
            for source, retrieved in freshness.items()
            if source in (SourceName.IMD_MARINE, SourceName.INCOIS_OCEAN_STATE)
        },
    )
    result.safety_flags = evaluate(result)
    flags = list(state.get("safety_flags") or []) + list(result.safety_flags)
    logger.info(
        "weather_risk evaluated",
        extra={"extra_fields": {"flags": [f.code for f in result.safety_flags]}},
    )
    return {
        "data_freshness": freshness,
        "weather_risk_result": result,
        "safety_flags": flags,
    }
