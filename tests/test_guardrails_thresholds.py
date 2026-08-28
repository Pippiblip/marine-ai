"""Exhaustive threshold boundary tests."""

from datetime import datetime, timezone

import pytest

from orca.guardrails.thresholds import (
    CYCLONE_NEAR_KM,
    SWELL_UNSAFE_M,
    WAVE_UNSAFE_M,
    WIND_UNSAFE_KT,
    evaluate,
)
from orca.schemas import Measurement, SourceName, WeatherRiskResult

NOW = datetime(2026, 8, 28, 6, 0, tzinfo=timezone.utc)


def measurement(value: float, unit: str = "m") -> Measurement:
    return Measurement(value=value, unit=unit, source=SourceName.IMD_MARINE, retrieved_at=NOW)


@pytest.mark.parametrize(
    ("field", "threshold", "unit", "code"),
    [
        ("wave_height", WAVE_UNSAFE_M, "m", "high_wave"),
        ("wind_speed", WIND_UNSAFE_KT, "kt", "high_wind"),
        ("cyclone_distance", CYCLONE_NEAR_KM, "km", "cyclone_proximity"),
        ("swell_surge", SWELL_UNSAFE_M, "m", "swell_surge"),
    ],
)
def test_exact_boundary_is_not_triggered(field: str, threshold: float, unit: str, code: str):
    result = WeatherRiskResult(**{field: measurement(threshold, unit)})
    assert all(flag.code != code for flag in evaluate(result))


@pytest.mark.parametrize(
    ("field", "threshold", "unit", "code"),
    [
        ("wave_height", WAVE_UNSAFE_M, "m", "high_wave"),
        ("wind_speed", WIND_UNSAFE_KT, "kt", "high_wind"),
        ("swell_surge", SWELL_UNSAFE_M, "m", "swell_surge"),
    ],
)
def test_value_below_threshold_is_not_triggered(field: str, threshold: float, unit: str, code: str):
    result = WeatherRiskResult(**{field: measurement(threshold - 0.01, unit)})
    assert all(flag.code != code for flag in evaluate(result))


def test_cyclone_distance_exactly_at_threshold_is_not_triggered():
    assert evaluate(WeatherRiskResult(cyclone_distance=measurement(CYCLONE_NEAR_KM, "km"))) == []


@pytest.mark.parametrize(
    ("field", "threshold", "unit", "code"),
    [
        ("wave_height", WAVE_UNSAFE_M, "m", "high_wave"),
        ("wind_speed", WIND_UNSAFE_KT, "kt", "high_wind"),
        ("swell_surge", SWELL_UNSAFE_M, "m", "swell_surge"),
    ],
)
def test_value_above_threshold_triggers_flag(field: str, threshold: float, unit: str, code: str):
    result = WeatherRiskResult(**{field: measurement(threshold + 0.01, unit)})
    flags = evaluate(result)
    assert [flag.code for flag in flags] == [code]
    assert flags[0].triggered_by[0].value == pytest.approx(threshold + 0.01)


def test_cyclone_distance_below_threshold_triggers_flag():
    flags = evaluate(WeatherRiskResult(cyclone_distance=measurement(CYCLONE_NEAR_KM - 0.01, "km")))
    assert flags[0].code == "cyclone_proximity"


def test_all_triggered_flags_preserve_metadata_and_order():
    result = WeatherRiskResult(
        wave_height=measurement(WAVE_UNSAFE_M + 1),
        wind_speed=measurement(WIND_UNSAFE_KT + 1, "kt"),
        cyclone_distance=measurement(CYCLONE_NEAR_KM - 1, "km"),
        swell_surge=measurement(SWELL_UNSAFE_M + 1),
    )
    flags = evaluate(result)
    assert [flag.code for flag in flags] == [
        "high_wave",
        "high_wind",
        "cyclone_proximity",
        "swell_surge",
    ]
    assert [flag.message_key for flag in flags] == [
        "danger_high_wave",
        "danger_high_wind",
        "danger_cyclone",
        "warn_swell",
    ]
    assert [flag.severity.value for flag in flags] == ["danger", "danger", "danger", "warning"]
    assert all(flag.triggered_by and flag.threshold_repr for flag in flags)


def test_missing_readings_are_safe_to_evaluate():
    assert evaluate(WeatherRiskResult()) == []
