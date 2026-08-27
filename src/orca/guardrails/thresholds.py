"""Deterministic safety verdicts based on hard-coded thresholds."""

from orca.config import settings
from orca.schemas import Measurement, SafetyFlag, Severity, WeatherRiskResult

# SAFETY: These constants define go/no-go. Change only with review.
WAVE_UNSAFE_M = settings.wave_unsafe_m  # default 2.5
WIND_UNSAFE_KT = settings.wind_unsafe_kt  # default 25
CYCLONE_NEAR_KM = settings.cyclone_near_km  # default 300
SWELL_UNSAFE_M = settings.swell_unsafe_m  # default 2.0


def evaluate(wr: WeatherRiskResult) -> list[SafetyFlag]:
    """
    Evaluate a weather result against thresholds and return triggered flags.

    Pure function: takes structured data, returns deterministic safety flags.
    No I/O, no LLM, fully unit-testable. Each flag identifies which measurement
    tripped which rule.

    Args:
        wr: WeatherRiskResult with optional Measurement fields.

    Returns:
        List of SafetyFlag objects (may be empty if all readings are safe).

    """
    flags: list[SafetyFlag] = []

    def add_flag(
        code: str,
        severity: Severity,
        message_key: str,
        measurement: Measurement,
        rule: str,
    ) -> None:
        flags.append(
            SafetyFlag(
                code=code,
                severity=severity,
                message_key=message_key,
                triggered_by=[measurement],
                threshold_repr=rule,
            )
        )

    # SAFETY: wave height
    if wr.wave_height and wr.wave_height.value > WAVE_UNSAFE_M:
        add_flag(
            "high_wave",
            Severity.DANGER,
            "danger_high_wave",
            wr.wave_height,
            f"wave_height > {WAVE_UNSAFE_M} m",
        )

    # SAFETY: wind speed
    if wr.wind_speed and wr.wind_speed.value > WIND_UNSAFE_KT:
        add_flag(
            "high_wind",
            Severity.DANGER,
            "danger_high_wind",
            wr.wind_speed,
            f"wind_speed > {WIND_UNSAFE_KT} kt",
        )

    # SAFETY: cyclone proximity
    if wr.cyclone_distance and wr.cyclone_distance.value < CYCLONE_NEAR_KM:
        add_flag(
            "cyclone_proximity",
            Severity.DANGER,
            "danger_cyclone",
            wr.cyclone_distance,
            f"cyclone_distance < {CYCLONE_NEAR_KM} km",
        )

    # SAFETY: swell surge
    if wr.swell_surge and wr.swell_surge.value > SWELL_UNSAFE_M:
        add_flag(
            "swell_surge",
            Severity.WARNING,
            "warn_swell",
            wr.swell_surge,
            f"swell_surge > {SWELL_UNSAFE_M} m",
        )

    return flags
