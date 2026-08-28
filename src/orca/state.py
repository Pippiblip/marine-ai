"""
The shared LangGraph state object for ORCA.

One instance of PlatformState exists per request/conversation and is passed
through all nodes. Each node reads what it needs and writes only its own slice.
"""

from typing import List, Literal, Optional, TypedDict

from orca.schemas import (
    GeoPoint,
    GeospatialResult,
    MarineDataResult,
    OceanAnalyticsResult,
    SafetyFlag,
    WeatherRiskResult,
)


class PlatformState(TypedDict, total=False):
    """Shared orchestration state for a single query.

    All nodes read what they need and write only their designated slice.
    No overwrites across node boundaries.
    """

    # --- Set by Channel Gateway ---
    query_text: str  # transcribed AND translated to English
    source_lang: str  # e.g. "ta-IN", "hi-IN", "en-IN"
    channel: Literal["web", "whatsapp", "ivr"]
    user_location: Optional[GeoPoint]
    cell_id: str  # fixture/data cell selected by the channel
    force_error: bool  # kill every data tool (legacy demo switch)
    force_error_sources: List[str]  # e.g. ["imd_marine"]
    audio_id: str  # mock ASR key from the web client
    trace_id: str  # per-run id for logging

    # --- Set by Router ---
    intent: str  # "pfz_nearest" | "safety_check" | ...
    subtasks: List[str]  # agent node names to run

    # --- Set by specialists (each writes only its own slice) ---
    marine_data_result: Optional[MarineDataResult]
    weather_risk_result: Optional[WeatherRiskResult]
    geospatial_result: Optional[GeospatialResult]
    ocean_analytics_result: Optional[OceanAnalyticsResult]

    # --- Safety + freshness (critical for Synthesis and Guardrail) ---
    safety_flags: List[SafetyFlag]
    data_freshness: dict  # source: SourceName -> last successful fetch time (datetime)

    # --- Set by Guardrail ---
    guardrail_status: Literal["ok", "stale", "failed"]
    guardrail_notes: List[str]  # machine reasons for logging + template selection

    # --- Set by Synthesis ---
    final_response_text: str  # English answer that will be spoken
    response_lang_text: str  # final_response_text translated back to source_lang
    citations: List[str]  # e.g. ["INCOIS PFZ advisory @ 2026-09-20 06:00 IST"]
