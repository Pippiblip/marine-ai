"""Deterministic geospatial specialist."""

from __future__ import annotations

from datetime import datetime, timezone

from orca.geo.distance import bearing_deg, haversine_km
from orca.geo.geofence import is_near_imbl_buffer
from orca.schemas import GeoPoint, GeospatialResult, Measurement, SourceName
from orca.state import PlatformState


def geospatial_node(state: PlatformState) -> dict:
    """Select the nearest PFZ and calculate boundary proximity."""
    location = state.get("user_location")
    marine = state.get("marine_data_result")
    if location is None:
        return {"geospatial_result": GeospatialResult()}

    user_point = (
        location if isinstance(location, GeoPoint) else GeoPoint(lat=location[0], lon=location[1])
    )
    nearest = None
    nodes = list(marine.pfz_nodes) if marine else []
    if nodes:
        nearest = min(nodes, key=lambda node: haversine_km(user_point, node.location))
    distance = None
    bearing = None
    now = datetime.now(timezone.utc)
    if nearest:
        distance_value = haversine_km(user_point, nearest.location)
        bearing = bearing_deg(user_point, nearest.location)
        distance = Measurement(
            value=distance_value,
            unit="km",
            source=SourceName.INCOIS_PFZ,
            retrieved_at=nearest.depth.retrieved_at if nearest.depth else now,
        )
        nearest = nearest.model_copy(update={"distance_km": distance, "bearing_deg": bearing})
    near_boundary, boundary_distance = is_near_imbl_buffer(user_point, buffer_km=5.0)
    boundary_measurement = Measurement(
        value=boundary_distance,
        unit="km",
        source=SourceName.MOCK,
        retrieved_at=now,
    )
    return {
        "geospatial_result": GeospatialResult(
            nearest_pfz=nearest,
            distance_km=distance,
            bearing_deg=bearing,
            inside_imbl_buffer=near_boundary,
            imbl_distance_km=boundary_measurement,
        )
    }
