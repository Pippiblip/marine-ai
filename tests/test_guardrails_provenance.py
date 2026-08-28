"""Number provenance and fixed template tests."""

from datetime import datetime, timezone

from orca.guardrails.provenance import collect_allowed, verify
from orca.guardrails.templates import render
from orca.schemas import Measurement, SourceName

NOW = datetime(2026, 8, 28, 6, 0, tzinfo=timezone.utc)


def wave(value: float) -> Measurement:
    return Measurement(value=value, unit="m", source=SourceName.IMD_MARINE, retrieved_at=NOW)


def test_clean_draft_and_rounding_pass():
    measurements = [wave(2.5), wave(3.6)]
    assert collect_allowed(measurements) == {"2", "2.5", "3.6", "4"}
    assert verify("Wave height is 2.5 m, roughly 4 m at the peak.", measurements) == (True, [])


def test_stray_number_is_rejected():
    valid, offending = verify("Wave height is 2.5 m and wind is 40 kt.", [wave(2.5)])
    assert not valid
    assert offending == ["40"]


def test_citation_date_and_time_are_metadata():
    assert verify("Reading from 2026-08-28 at 06:00 UTC is 2.5 m.", [wave(2.5)]) == (True, [])


def test_signed_and_scientific_measurement_values_are_supported():
    negative = Measurement(value=-2.5, unit="m", source=SourceName.IMD_MARINE, retrieved_at=NOW)
    scientific = Measurement(value=1e-3, unit="m", source=SourceName.IMD_MARINE, retrieved_at=NOW)
    assert verify("Values are -2.5 m and 0.001 m.", [negative, scientific]) == (True, [])


def test_repeated_stray_numbers_are_reported_each_time():
    valid, offending = verify("Readings 9 m and 9 kt are unavailable.", [wave(2.5)])
    assert not valid
    assert offending == ["9", "9"]


def test_templates_are_fixed_and_renderable():
    values = {
        "value": 3.0,
        "limit": 2.5,
        "caption": "as of now",
        "wave": 1.0,
        "wind": 10.0,
        "what": "weather",
        "have": "wave data",
        "missing": "wind data",
        "summary": "conditions are unknown",
    }
    for key in (
        "danger_high_wave",
        "danger_high_wind",
        "danger_cyclone",
        "warn_swell",
        "all_clear",
        "data_unavailable",
        "data_stale",
        "partial_data",
        "location_unknown",
    ):
        text = render(key, **values)
        assert text
    assert "I won't guess about your safety" in render("data_unavailable", what="weather")
