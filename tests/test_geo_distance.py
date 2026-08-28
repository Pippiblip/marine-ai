"""Known great-circle distance and bearing checks."""

import pytest

from orca.geo.distance import bearing_deg, haversine_km
from orca.schemas import GeoPoint


def test_one_degree_on_equator():
    origin = GeoPoint(lat=0, lon=0)
    east = GeoPoint(lat=0, lon=1)
    assert haversine_km(origin, east) == pytest.approx(111.195, abs=0.01)
    assert bearing_deg(origin, east) == pytest.approx(90.0)


def test_bearing_is_normalized():
    assert 0 <= bearing_deg(GeoPoint(lat=10, lon=10), GeoPoint(lat=11, lon=10)) < 360
