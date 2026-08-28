"""Polygon and boundary-buffer checks."""

import json
from pathlib import Path

import pytest

from orca.geo.geofence import (
    closest_distance_to_polygon_km,
    is_near_imbl_buffer,
    load_geojson_polygon,
    point_in_polygon,
)
from orca.schemas import GeoPoint

POLYGON = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]


def test_inside_outside_and_boundary():
    assert point_in_polygon(GeoPoint(lat=0.5, lon=0.5), POLYGON)
    assert not point_in_polygon(GeoPoint(lat=2, lon=2), POLYGON)
    assert point_in_polygon(GeoPoint(lat=0, lon=0.5), POLYGON)
    assert not point_in_polygon(GeoPoint(lat=0, lon=0), [])


def test_distance_uses_nearest_edge_not_only_vertices():
    distance = closest_distance_to_polygon_km(GeoPoint(lat=0.5, lon=1.1), POLYGON)
    assert distance == pytest.approx(11.13, abs=0.2)


def test_concave_polygon_and_reversed_winding():
    concave = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (1.0, 1.0), (0.0, 2.0)]
    assert point_in_polygon(GeoPoint(lat=0.5, lon=1.0), concave)
    assert not point_in_polygon(GeoPoint(lat=1.5, lon=1.0), concave)
    assert point_in_polygon(GeoPoint(lat=0.5, lon=1.0), list(reversed(concave)))


def test_geojson_load_and_buffer(tmp_path):
    path = tmp_path / "imbl.geojson"
    path.write_text(
        json.dumps({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [POLYGON]}}),
        encoding="utf-8",
    )
    assert load_geojson_polygon(path) == POLYGON
    near, distance = is_near_imbl_buffer(GeoPoint(lat=0.5, lon=1.1), 12, path)
    assert near
    assert distance == pytest.approx(11.13, abs=0.2)


def test_default_imbl_fixture_has_inside_and_outside_points():
    polygon = load_geojson_polygon(Path(__file__).parents[1] / "src/orca/fixtures/geo/imbl.geojson")
    assert polygon is not None
    assert point_in_polygon(GeoPoint(lat=9.5, lon=79.8), polygon)
    near_boundary, _ = is_near_imbl_buffer(GeoPoint(lat=9.0, lon=79.8), 0)
    far_from_boundary, _ = is_near_imbl_buffer(GeoPoint(lat=11.0, lon=79.8), 0)
    assert near_boundary
    assert not far_from_boundary
