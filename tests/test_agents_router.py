"""Router maps MVP queries to the fixed intent and subtask lists."""

from orca.agents.router import router_node


def test_pfz_query_maps_to_marine_geo_weather():
    """Fishing-zone questions should plan the three PFZ specialists."""
    out = router_node({"query_text": "Where is the nearest fishing zone?"})
    assert out["intent"] == "pfz_nearest"
    assert out["subtasks"] == ["marine_data", "geospatial", "weather_risk"]


def test_safety_query_maps_to_weather_and_geo():
    """Safety questions should plan weather then geospatial."""
    out = router_node({"query_text": "Is it safe to go out tomorrow morning?"})
    assert out["intent"] == "safety_check"
    assert out["subtasks"] == ["weather_risk", "geospatial"]


def test_unknown_query_still_returns_a_label():
    """Out-of-scope text must not crash classification."""
    out = router_node({"query_text": "hello there"})
    assert out["intent"] in {
        "pfz_nearest",
        "safety_check",
        "boundary_check",
        "conditions_summary",
    }
