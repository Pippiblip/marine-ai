"""Tests for geofencing and boundary checks."""

from pathlib import Path

from orca.geo.geofence import is_near_imbl_buffer, load_geojson_polygon, point_in_polygon
from orca.schemas import GeoPoint


def test_point_in_polygon_basic():
    """Simple square polygon contains the interior point."""
    polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    point = GeoPoint(lat=5.0, lon=5.0)
    assert point_in_polygon(point, polygon)


def test_point_outside_polygon_basic():
    """Point outside the polygon should be false."""
    polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    point = GeoPoint(lat=15.0, lon=15.0)
    assert not point_in_polygon(point, polygon)


def test_load_imbl_fixture():
    """The IMBL fixture should load as polygon data."""
    path = (
        Path(__file__).resolve().parents[1] / "src" / "orca" / "fixtures" / "geo" / "imbl.geojson"
    )
    polygon = load_geojson_polygon(path)
    assert polygon is not None
    assert len(polygon) > 3


def test_is_near_imbl_buffer_on_fixture():
    """Point near IMBL should report near/inside if the buffer is wide enough."""
    path = (
        Path(__file__).resolve().parents[1] / "src" / "orca" / "fixtures" / "geo" / "imbl.geojson"
    )
    point = GeoPoint(lat=8.0, lon=78.0)
    is_near, distance = is_near_imbl_buffer(point, buffer_km=1000.0, imbl_file=path)
    assert isinstance(is_near, bool)
    assert distance >= 0.0
