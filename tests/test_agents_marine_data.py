"""Marine data agent returns typed PFZ and chlorophyll measurements."""

from orca.agents.marine_data import marine_data_node
from orca.schemas import GeoPoint, SourceName


def test_calm_cell_returns_pfz_and_chlorophyll():
    """Calm fixtures yield at least one PFZ node and an EO reading."""
    out = marine_data_node(
        {
            "cell_id": "calm",
            "user_location": GeoPoint(lat=12.42, lon=79.40),
            "data_freshness": {},
        }
    )
    result = out["marine_data_result"]
    assert len(result.pfz_nodes) >= 1
    assert result.pfz_nodes[0].depth is not None
    assert result.chlorophyll is not None
    assert SourceName.INCOIS_PFZ in result.source_freshness
    assert SourceName.ISRO_CHLOROPHYLL in result.source_freshness


def test_unknown_cell_is_empty():
    """Unknown cells yield empty PFZ lists without error."""
    out = marine_data_node({"cell_id": "missing-cell", "data_freshness": {}})
    assert out["marine_data_result"].pfz_nodes == []
