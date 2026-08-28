"""Channel gateway: normalize inbound audio/text into graph state."""

from __future__ import annotations

from typing import Optional, Union

from orca.logging import generate_trace_id, get_logger, set_trace_id
from orca.schemas import GeoPoint
from orca.speech.factory import get_speech
from orca.state import PlatformState

logger = get_logger(__name__)


def _as_geo(location: Union[GeoPoint, tuple, list, None]) -> Optional[GeoPoint]:
    """Accept GeoPoint or (lat, lon) from the API layer."""
    if location is None:
        return None
    if isinstance(location, GeoPoint):
        return location
    return GeoPoint(lat=float(location[0]), lon=float(location[1]))


def channel_gateway_node(state: PlatformState) -> dict:
    """ASR, language, translate-to-English, resolve location, assign trace_id."""
    speech = get_speech()
    trace_id = state.get("trace_id") or generate_trace_id()
    set_trace_id(trace_id)
    source_lang = state.get("source_lang") or "en-IN"
    query = (state.get("query_text") or "").strip()
    audio_id = state.get("audio_id")
    if audio_id and not query:
        blob = audio_id.encode("utf-8")
        source_lang = speech.detect_language(blob)
        native = speech.asr(blob, source_lang)
        query = speech.translate(native, source_lang, "en-IN")
    logger.info("channel_gateway ready", extra={"extra_fields": {"trace_id": trace_id}})
    return {
        "query_text": query,
        "source_lang": source_lang,
        "channel": state.get("channel", "web"),
        "user_location": _as_geo(state.get("user_location")),
        "cell_id": state.get("cell_id", "calm"),
        "force_error": bool(state.get("force_error", False)),
        "force_error_sources": list(state.get("force_error_sources") or []),
        "data_freshness": dict(state.get("data_freshness") or {}),
        "safety_flags": list(state.get("safety_flags") or []),
        "trace_id": trace_id,
    }
