"""Weather & Risk is the only writer of SafetyFlags."""

from orca.agents.weather_risk import weather_risk_node
from orca.schemas import GeoPoint, Severity


def test_cyclone_cell_raises_danger():
    """Above-threshold fixtures must produce a DANGER flag."""
    out = weather_risk_node(
        {
            "cell_id": "cyclone",
            "user_location": GeoPoint(lat=12.42, lon=79.40),
            "data_freshness": {},
            "safety_flags": [],
        }
    )
    result = out["weather_risk_result"]
    assert result.wave_height is not None
    assert result.wave_height.value == 3.4
    assert any(flag.severity == Severity.DANGER for flag in result.safety_flags)
    assert any(flag.code == "high_wave" for flag in result.safety_flags)


def test_calm_cell_has_no_flags():
    """Below-threshold fixtures must not raise flags."""
    out = weather_risk_node(
        {
            "cell_id": "calm",
            "user_location": GeoPoint(lat=12.42, lon=79.40),
            "data_freshness": {},
            "safety_flags": [],
        }
    )
    assert out["weather_risk_result"].safety_flags == []


def test_missing_imd_does_not_crash():
    """A killed IMD source writes no reading and no flag."""
    out = weather_risk_node(
        {
            "cell_id": "calm",
            "force_error_sources": ["imd_marine"],
            "data_freshness": {},
            "safety_flags": [],
        }
    )
    result = out["weather_risk_result"]
    assert result.wave_height is None
    assert result.safety_flags == []
