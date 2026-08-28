"""Shared helpers for specialist nodes."""

from __future__ import annotations

from orca.schemas import BoundingBox, GeoPoint, SourceName
from orca.state import PlatformState


def force_error_for(state: PlatformState, source: SourceName) -> bool:
    """Whether this run should force a tool error for ``source``."""
    if state.get("force_error"):
        return True
    names = state.get("force_error_sources") or []
    return source.value in names or source.name in names


def cell_id(state: PlatformState) -> str:
    """Fixture cell selected by the channel (calm / cyclone / unknown)."""
    return state.get("cell_id") or "calm"


def bbox_around(point: GeoPoint, delta: float = 0.25) -> BoundingBox:
    """Build a small cell around a GPS point."""
    return BoundingBox(
        min_lat=point.lat - delta,
        min_lon=point.lon - delta,
        max_lat=point.lat + delta,
        max_lon=point.lon + delta,
    )
