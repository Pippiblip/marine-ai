"""Evidence-bound response synthesis."""

from __future__ import annotations

from datetime import datetime, timezone

from orca.geo.distance import compass_8
from orca.guardrails.freshness import caption
from orca.guardrails.provenance import verify
from orca.guardrails.resilience import get_last_ok
from orca.guardrails.templates import TEMPLATES
from orca.guardrails.thresholds import (
    CYCLONE_NEAR_KM,
    SWELL_UNSAFE_M,
    WAVE_UNSAFE_M,
    WIND_UNSAFE_KT,
)
from orca.llm.factory import get_llm
from orca.logging import get_logger
from orca.schemas import Measurement, Severity, SourceName
from orca.speech.factory import get_speech
from orca.state import PlatformState
from orca.tools.imd import MarineWarningPayload

logger = get_logger(__name__)


def _threshold_tokens() -> set[str]:
    """Numeric tokens from hard-coded safety limits (not LLM-invented)."""
    tokens: set[str] = set()
    for value in (WAVE_UNSAFE_M, WIND_UNSAFE_KT, CYCLONE_NEAR_KM, SWELL_UNSAFE_M):
        tokens.add(f"{value:g}")
        tokens.add(f"{value:.1f}")
        tokens.add(f"{round(value)}")
    return tokens


def _measurements(state: PlatformState) -> list[Measurement]:
    values: list[Measurement] = []
    marine = state.get("marine_data_result")
    weather = state.get("weather_risk_result")
    geo = state.get("geospatial_result")
    if marine:
        values.extend(m for m in (marine.chlorophyll, marine.sst) if m is not None)
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
    if geo:
        if geo.distance_km:
            values.append(geo.distance_km)
        if geo.nearest_pfz and geo.nearest_pfz.depth:
            values.append(geo.nearest_pfz.depth)
        if geo.bearing_deg is not None:
            values.append(
                Measurement(
                    value=geo.bearing_deg,
                    unit="deg",
                    source=SourceName.INCOIS_PFZ,
                    retrieved_at=(
                        geo.distance_km.retrieved_at if geo.distance_km else datetime.now(timezone.utc)
                    ),
                )
            )
    for flag in state.get("safety_flags") or []:
        values.extend(flag.triggered_by)
    return values


def _last_known_clause(measurements: list[Measurement]) -> tuple[str, list[Measurement]]:
    last = get_last_ok(SourceName.IMD_MARINE)
    payload = last.payload if last else None
    if not isinstance(payload, MarineWarningPayload) or payload.wave_height is None:
        return "", measurements
    wave = payload.wave_height
    clause = TEMPLATES["last_known_clause"].format(
        value=f"{wave.value:g}",
        unit=wave.unit,
        caption=caption(wave),
    )
    return clause, measurements + [wave]


def _danger_draft(flag, measurements: list[Measurement]) -> str:
    measurement = flag.triggered_by[0]
    limit = WAVE_UNSAFE_M
    if flag.message_key == "danger_high_wind":
        limit = WIND_UNSAFE_KT
    elif flag.message_key == "danger_cyclone":
        return TEMPLATES[flag.message_key].format(
            value=f"{measurement.value:g}", caption=caption(measurement)
        )
    elif flag.message_key == "warn_swell":
        limit = SWELL_UNSAFE_M
    return TEMPLATES[flag.message_key].format(
        value=f"{measurement.value:g}",
        caption=caption(measurement),
        limit=f"{limit:g}",
    )


def synthesis_node(state: PlatformState) -> dict:
    """Produce a response only from guardrail-approved, source-backed facts."""
    measurements = _measurements(state)
    status = state.get("guardrail_status", "ok")
    flags = state.get("safety_flags") or []
    if status == "failed":
        last_known, measurements = _last_known_clause(measurements)
        draft = TEMPLATES["data_unavailable"].format(what="weather", last_known=last_known)
    elif status == "stale":
        measurement = next((m for m in measurements if m is not None), None)
        draft = TEMPLATES["data_stale"].format(
            what="marine", caption=caption(measurement) if measurement else "an unknown time"
        )
    elif any(flag.severity == Severity.DANGER for flag in flags):
        # SAFETY: verdict is the template; the LLM may not flip it.
        flag = next(flag for flag in flags if flag.severity == Severity.DANGER)
        draft = _danger_draft(flag, measurements)
        extras = [
            f
            for f in flags
            if f.severity == Severity.DANGER and f.message_key != flag.message_key
        ]
        if extras and extras[0].message_key == "danger_cyclone":
            cyc = extras[0].triggered_by[0]
            draft = (
                f"{draft} A cyclone is {cyc.value:g} km away ({caption(cyc)}). Stay ashore."
            )
    elif state.get("user_location") is None and state.get("intent") in {
        "pfz_nearest",
        "safety_check",
        "boundary_check",
    }:
        draft = TEMPLATES["location_unknown"]
    else:
        geo = state.get("geospatial_result")
        weather = state.get("weather_risk_result")
        marine = state.get("marine_data_result")
        if geo and geo.nearest_pfz and geo.distance_km and geo.bearing_deg is not None:
            node = geo.nearest_pfz
            facts = {
                "zone_name": "PFZ advisory",
                "distance": f"{geo.distance_km.value:.1f}",
                "bearing": compass_8(geo.bearing_deg),
                "depth": f"{node.depth.value:g}" if node.depth else "unknown",
                "condition": "productive",
            }
            draft = get_llm().narrate(facts, system="Use only these facts; add no numbers.")
            if marine and marine.chlorophyll:
                draft = (
                    f"{draft} Chlorophyll is {marine.chlorophyll.value:g} "
                    f"({caption(marine.chlorophyll)})."
                )
            src = geo.distance_km
            draft = f"{draft} Source: INCOIS PFZ advisory, {caption(src)}."
        elif weather and weather.wave_height and weather.wind_speed:
            draft = TEMPLATES["all_clear"].format(
                wave=f"{weather.wave_height.value:g}",
                wind=f"{weather.wind_speed.value:g}",
                caption=caption(weather.wave_height),
            )
        elif marine and not (marine.pfz_nodes):
            draft = TEMPLATES["data_unavailable"].format(
                what="fishing-zone", last_known=""
            )
        else:
            draft = (
                TEMPLATES["location_unknown"]
                if state.get("user_location") is None
                else TEMPLATES["data_unavailable"].format(what="requested", last_known="")
            )
    valid, offenders = verify(draft, measurements, extra_allowed=_threshold_tokens())
    if not valid and status == "ok":
        logger.warning("provenance rejected draft", extra={"extra_fields": {"offenders": offenders}})
        draft = TEMPLATES["data_unavailable"].format(what="verified", last_known="")
    speech = get_speech()
    source_lang = state.get("source_lang") or "en-IN"
    translated = speech.translate(draft, "en-IN", source_lang)
    citations = []
    for measurement in measurements:
        citation = f"{measurement.source.value}, {caption(measurement)}"
        if citation not in citations:
            citations.append(citation)
    return {
        "final_response_text": draft,
        "response_lang_text": translated,
        "citations": citations,
    }
