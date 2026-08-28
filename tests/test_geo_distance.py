"""Tests for geospatial distance and bearing calculations."""

from orca.geo.distance import bearing_deg, haversine_km
from orca.schemas import GeoPoint


def test_haversine_known_pair():
    """Distance from Chennai to Kochi is about 600 km."""
    p1 = GeoPoint(lat=13.0827, lon=80.2707)
    p2 = GeoPoint(lat=9.9312, lon=76.2673)
    distance = haversine_km(p1, p2)
    assert 550 < distance < 700


def test_bearing_known_pair():
    """Bearing from Chennai to Kochi should be roughly west-southwest."""
    p1 = GeoPoint(lat=13.0827, lon=80.2707)
    p2 = GeoPoint(lat=9.9312, lon=76.2673)
    bearing = bearing_deg(p1, p2)
    assert 220 < bearing < 270


def test_haversine_zero_distance():
    """A point to itself should have zero distance."""
    p = GeoPoint(lat=12.0, lon=80.0)
    assert haversine_km(p, p) == 0.0
