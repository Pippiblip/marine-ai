"""Geospatial specialist picks the nearest PFZ and checks IMBL proximity."""

from datetime import datetime, timezone

from orca.agents.geospatial import geospatial_node
from orca.schemas import GeoPoint, MarineDataResult, Measurement, PFZNode, SourceName


def _node(lat: float, lon: float, depth: float = 18.0) -> PFZNode:
    now = datetime.now(timezone.utc)
    return PFZNode(
        location=GeoPoint(lat=lat, lon=lon),
        depth=Measurement(
            value=depth,
            unit="m_depth",
            source=SourceName.INCOIS_PFZ,
            retrieved_at=now,
        ),
        valid_date=now,
    )


def test_selects_nearest_node():
    """The closer of two PFZ nodes is selected with a distance measurement."""
    user = GeoPoint(lat=12.42, lon=79.40)
    marine = MarineDataResult(
        pfz_nodes=[
            _node(12.5, 79.5),
            _node(13.1, 80.2),
        ]
    )
    out = geospatial_node({"user_location": user, "marine_data_result": marine})
    geo = out["geospatial_result"]
    assert geo.nearest_pfz is not None
    assert geo.nearest_pfz.location.lat == 12.5
    assert geo.distance_km is not None
    assert 10 < geo.distance_km.value < 20


def test_missing_location_empty_result():
    """No GPS yields an empty geospatial result without crashing."""
    out = geospatial_node({"user_location": None})
    assert out["geospatial_result"].nearest_pfz is None
