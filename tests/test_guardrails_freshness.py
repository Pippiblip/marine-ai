"""Freshness window and citation tests."""

from datetime import datetime, timedelta, timezone

from orca.guardrails.freshness import PFZ_MAX_AGE_S, SAFETY_MAX_AGE_S, caption, is_fresh
from orca.schemas import Measurement, SourceName

NOW = datetime(2026, 8, 28, 6, 30, tzinfo=timezone.utc)


def reading(age_seconds: float) -> Measurement:
    return Measurement(
        value=2.5,
        unit="m",
        source=SourceName.IMD_MARINE,
        retrieved_at=NOW - timedelta(seconds=age_seconds),
    )


def test_safety_window_boundaries():
    assert is_fresh(reading(SAFETY_MAX_AGE_S), max_age_s=SAFETY_MAX_AGE_S, now=NOW)
    assert not is_fresh(reading(SAFETY_MAX_AGE_S + 1), max_age_s=SAFETY_MAX_AGE_S, now=NOW)


def test_pfz_window_boundaries():
    assert is_fresh(reading(PFZ_MAX_AGE_S), max_age_s=PFZ_MAX_AGE_S, now=NOW)
    assert not is_fresh(reading(PFZ_MAX_AGE_S + 1), max_age_s=PFZ_MAX_AGE_S, now=NOW)


def test_future_reading_is_fresh():
    assert is_fresh(reading(-10), max_age_s=SAFETY_MAX_AGE_S, now=NOW)


def test_caption_contains_utc_timestamp_and_age():
    text = caption(reading(45 * 60), NOW)
    assert text == "as of 2026-08-28 05:45 UTC (45 min ago)"
