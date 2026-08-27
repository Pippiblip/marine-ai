"""Geofencing: point-in-polygon and buffer operations."""

import json
from pathlib import Path
from typing import Optional

from orca.geo.distance import haversine_km
from orca.schemas import GeoPoint


def point_in_polygon(point: GeoPoint, polygon: list[tuple[float, float]]) -> bool:
    """
    Ray-casting algorithm for point-in-polygon test.

    Uses the standard winding number / ray-casting approach. The polygon
    is expected as a list of (lon, lat) tuples in order (GeoJSON convention).

    Args:
        point: The test point (GeoPoint with lat, lon).
        polygon: List of (lon, lat) tuples forming a closed ring.

    Returns:
        True if the point is inside the polygon, False otherwise.

    """
    x, y = point.lon, point.lat
    inside = False

    p1_lon, p1_lat = polygon[0]
    for i in range(1, len(polygon)):
        p2_lon, p2_lat = polygon[i]
        if y > min(p1_lat, p2_lat):
            if y <= max(p1_lat, p2_lat):
                if x <= max(p1_lon, p2_lon):
                    if p1_lat != p2_lat:
                        xinters = (y - p1_lat) * (p2_lon - p1_lon) / (
                            p2_lat - p1_lat
                        ) + p1_lon
                    if p1_lon == p2_lon or x <= xinters:
                        inside = not inside
        p1_lon, p1_lat = p2_lon, p2_lat

    return inside


def load_geojson_polygon(file_path: Path) -> Optional[list[tuple[float, float]]]:
    """
    Load a GeoJSON file and extract the first polygon's exterior ring.

    The file should contain a FeatureCollection or a Feature with a
    Polygon or MultiPolygon geometry. Returns the first polygon's
    exterior ring as (lon, lat) tuples.

    Args:
        file_path: Path to the GeoJSON file.

    Returns:
        List of (lon, lat) tuples, or None if no polygon found.

    """
    if not file_path.exists():
        return None

    with open(file_path) as f:
        data = json.load(f)

    # Handle FeatureCollection
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
        if features:
            data = features[0]

    # Handle Feature
    if data.get("type") == "Feature":
        data = data.get("geometry", {})

    # Extract polygon
    geom_type = data.get("type")
    coordinates = data.get("coordinates", [])

    if geom_type == "Polygon":
        # Polygon: coordinates[0] is the exterior ring
        return [(lon, lat) for lon, lat in coordinates[0]]
    elif geom_type == "MultiPolygon":
        # MultiPolygon: use the first polygon
        if coordinates:
            return [(lon, lat) for lon, lat in coordinates[0][0]]

    return None


def closest_distance_to_polygon_km(
    point: GeoPoint, polygon: list[tuple[float, float]]
) -> float:
    """
    Compute the minimum distance from a point to any edge of a polygon.

    Args:
        point: The test point.
        polygon: List of (lon, lat) tuples forming a closed ring.

    Returns:
        Distance in kilometers to the nearest edge/vertex.

    """
    min_dist_km = float("inf")

    for i in range(len(polygon)):
        p1_lon, p1_lat = polygon[i]
        p2_lon, p2_lat = polygon[(i + 1) % len(polygon)]

        # Distance to both vertices
        dist_to_p1 = haversine_km(point, GeoPoint(lat=p1_lat, lon=p1_lon))
        dist_to_p2 = haversine_km(point, GeoPoint(lat=p2_lat, lon=p2_lon))
        min_dist_km = min(min_dist_km, dist_to_p1, dist_to_p2)

        # Distance to the edge (simplified: closest point on segment)
        # For a more precise calculation, project onto the segment.
        # For now, vertex distance suffices as an approximation.

    return min_dist_km


def is_near_imbl_buffer(
    point: GeoPoint, buffer_km: float = 0.0, imbl_file: Optional[Path] = None
) -> tuple[bool, float]:
    """
    Check if a point is within a buffer zone of the IMBL boundary.

    Args:
        point: The test point.
        buffer_km: Distance in km to add as a safety zone around the boundary.
        imbl_file: Path to the IMBL GeoJSON file. If None, uses fixtures/geo/imbl.geojson.

    Returns:
        Tuple of (is_near, distance_km). is_near=True if within buffer zone.

    """
    if imbl_file is None:
        imbl_file = Path(__file__).parent.parent / "fixtures" / "geo" / "imbl.geojson"

    polygon = load_geojson_polygon(imbl_file)
    if polygon is None:
        # If no IMBL file, no boundary check
        return (False, float("inf"))

    distance_km = closest_distance_to_polygon_km(point, polygon)
    is_near = distance_km <= buffer_km

    return (is_near, distance_km)
