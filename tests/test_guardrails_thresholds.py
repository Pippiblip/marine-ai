"""Tests for safety threshold evaluation."""

from datetime import datetime, timezone

from orca.guardrails.thresholds import (
    CYCLONE_NEAR_KM,
    SWELL_UNSAFE_M,
    WAVE_UNSAFE_M,
    WIND_UNSAFE_KT,
    evaluate,
)
from orca.schemas import Measurement, Severity, SourceName, WeatherRiskResult


def _measurement(value: float, unit: str, source: SourceName = SourceName.MOCK):
    return Measurement(
        value=value,
        unit=unit,
        source=source,
        retrieved_at=datetime(2026, 9, 20, 6, 0, tzinfo=timezone.utc),
    )


def test_thresholds_no_flag_below_limits():
    """Safe values should not trigger safety flags."""
    result = WeatherRiskResult(
        wave_height=_measurement(1.2, "m"),
        wind_speed=_measurement(10.0, "kt"),
        cyclone_distance=_measurement(500.0, "km"),
        swell_surge=_measurement(0.5, "m"),
    )
    flags = evaluate(result)
    assert flags == []


def test_thresholds_flag_above_limits():
    """Values above thresholds should trigger danger flags."""
    result = WeatherRiskResult(
        wave_height=_measurement(WAVE_UNSAFE_M + 0.1, "m"),
        wind_speed=_measurement(WIND_UNSAFE_KT + 1.0, "kt"),
        cyclone_distance=_measurement(CYCLONE_NEAR_KM - 10.0, "km"),
        swell_surge=_measurement(SWELL_UNSAFE_M + 0.1, "m"),
    )
    flags = evaluate(result)
    assert len(flags) >= 4
    assert any(flag.severity == Severity.DANGER for flag in flags)


def test_thresholds_exact_boundary_documented():
    """Exact boundary values are treated as not exceeding the threshold."""
    result = WeatherRiskResult(
        wave_height=_measurement(WAVE_UNSAFE_M, "m"),
        wind_speed=_measurement(WIND_UNSAFE_KT, "kt"),
        cyclone_distance=_measurement(CYCLONE_NEAR_KM, "km"),
        swell_surge=_measurement(SWELL_UNSAFE_M, "m"),
    )
    flags = evaluate(result)
    assert flags == []


def test_thresholds_missing_reading_no_crash():
    """Missing readings should not crash threshold evaluation."""
    result = WeatherRiskResult()
    flags = evaluate(result)
    assert flags == []
