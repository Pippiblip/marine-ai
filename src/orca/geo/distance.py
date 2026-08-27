"""Haversine distance and bearing calculations."""

import math
from orca.schemas import GeoPoint

# Earth's mean radius in kilometers
EARTH_RADIUS_KM = 6371.0


def haversine_km(p1: GeoPoint, p2: GeoPoint) -> float:
    """
    Calculate the great-circle distance between two points using haversine.

    Args:
        p1: First point (lat, lon).
        p2: Second point (lat, lon).

    Returns:
        Distance in kilometers.

    """
    lat1_rad = math.radians(p1.lat)
    lon1_rad = math.radians(p1.lon)
    lat2_rad = math.radians(p2.lat)
    lon2_rad = math.radians(p2.lon)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def bearing_deg(p1: GeoPoint, p2: GeoPoint) -> float:
    """
    Calculate the initial bearing from p1 to p2 (true north).

    Args:
        p1: Starting point (lat, lon).
        p2: Destination point (lat, lon).

    Returns:
        Bearing in degrees (0–360), where 0/360 is north, 90 is east, 180 is south, 270 is west.

    """
    lat1_rad = math.radians(p1.lat)
    lon1_rad = math.radians(p1.lon)
    lat2_rad = math.radians(p2.lat)
    lon2_rad = math.radians(p2.lon)

    dlon = lon2_rad - lon1_rad

    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
        lat2_rad
    ) * math.cos(dlon)

    bearing_rad = math.atan2(y, x)
    bearing = math.degrees(bearing_rad)

    # Normalize to 0–360
    return (bearing + 360) % 360
