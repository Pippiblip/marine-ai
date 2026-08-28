"""LangGraph composition for the ORCA request pipeline."""

from __future__ import annotations

from typing import Any, Optional, Union

from langgraph.graph import END, START, StateGraph

from orca.agents.channel_gateway import channel_gateway_node
from orca.agents.geospatial import geospatial_node
from orca.agents.marine_data import marine_data_node
from orca.agents.ocean_analytics import ocean_analytics_node
from orca.agents.router import router_node
from orca.agents.synthesis import synthesis_node
from orca.agents.weather_risk import weather_risk_node
from orca.guardrails.gate import guardrail_node
from orca.schemas import GeoPoint
from orca.state import PlatformState

# Import adapters so the registry is populated before the first query.
import orca.tools  # noqa: F401

# Near the calm PFZ fixture (~12 km from 12.5N, 79.5E).
DEFAULT_LOCATION = GeoPoint(lat=12.42, lon=79.40)


def _after_router(state: PlatformState) -> str:
    """Choose the first specialist from the router's fixed plan."""
    intent = state.get("intent")
    if intent == "pfz_nearest":
        return "marine_data"
    if intent in ("safety_check", "conditions_summary"):
        return "weather_risk"
    return "geospatial"


def _after_geospatial(state: PlatformState) -> str:
    """Run weather after geospatial only for the PFZ path."""
    return "weather_risk" if state.get("intent") == "pfz_nearest" else "guardrail"


def build_graph() -> Any:
    """Build and compile the request graph."""
    graph = StateGraph(PlatformState)
    graph.add_node("channel_gateway", channel_gateway_node)
    graph.add_node("router", router_node)
    graph.add_node("marine_data", marine_data_node)
    graph.add_node("weather_risk", weather_risk_node)
    graph.add_node("geospatial", geospatial_node)
    graph.add_node("ocean_analytics", ocean_analytics_node)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_edge(START, "channel_gateway")
    graph.add_edge("channel_gateway", "router")
    graph.add_conditional_edges(
        "router",
        _after_router,
        {"marine_data": "marine_data", "weather_risk": "weather_risk", "geospatial": "geospatial"},
    )
    graph.add_edge("marine_data", "geospatial")
    graph.add_conditional_edges(
        "geospatial",
        _after_geospatial,
        {
            "weather_risk": "weather_risk",
            "guardrail": "guardrail",
        },
    )
    graph.add_edge("weather_risk", "guardrail")
    graph.add_edge("guardrail", "synthesis")
    graph.add_edge("synthesis", END)
    return graph.compile()


orca_graph = build_graph()


def run_query(
    query_text: str = "",
    *,
    user_location: Optional[Union[GeoPoint, tuple[float, float]]] = DEFAULT_LOCATION,
    cell_id: str = "calm",
    force_error: bool = False,
    force_error_sources: Optional[list[str]] = None,
    source_lang: str = "en-IN",
    channel: str = "web",
    audio_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> PlatformState:
    """Run a text or mock-audio query through the complete offline graph."""
    location: Optional[GeoPoint]
    if user_location is None:
        location = None
    elif isinstance(user_location, GeoPoint):
        location = user_location
    else:
        location = GeoPoint(lat=float(user_location[0]), lon=float(user_location[1]))
    payload: dict[str, Any] = {
        "query_text": query_text,
        "user_location": location,
        "cell_id": cell_id,
        "force_error": force_error,
        "force_error_sources": list(force_error_sources or []),
        "source_lang": source_lang,
        "channel": channel,
    }
    if audio_id:
        payload["audio_id"] = audio_id
    if trace_id:
        payload["trace_id"] = trace_id
    return orca_graph.invoke(payload)
