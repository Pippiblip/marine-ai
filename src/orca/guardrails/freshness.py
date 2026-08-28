"""Freshness checks and age captions for measurements."""

from datetime import datetime, timezone

from orca.config import settings
from orca.schemas import Measurement

# Freshness windows (can be overridden via env)
SAFETY_MAX_AGE_S = settings.freshness_max_min_safety * 60  # default 30 min → seconds
PFZ_MAX_AGE_S = settings.freshness_max_hours_pfz * 3600  # default 6 hours → seconds


def is_fresh(m: Measurement, *, max_age_s: int, now: datetime = None) -> bool:
    """
    Check if a measurement is fresh (not older than max_age_s).

    Args:
        m: The measurement to check.
        max_age_s: Maximum acceptable age in seconds.
        now: Reference time (defaults to now UTC if not provided).

    Returns:
        True if the measurement age is <= max_age_s, False otherwise.

    """
    if now is None:
        now = datetime.now(timezone.utc)
    return m.age_seconds(now) <= max_age_s


def caption(m: Measurement, now: datetime = None) -> str:
    """
    Generate a human-readable "as of" caption for a measurement.

    Used in citations and failure messages. Always includes the time
    so the user knows how stale the data is.

    Args:
        m: The measurement to caption.
        now: Reference time (defaults to now UTC if not provided).

    Returns:
        A string like "as of 2026-09-20 06:00 UTC (45 min ago)".

    """
    if now is None:
        now = datetime.now(timezone.utc)

    mins = int(m.age_seconds(now) // 60)
    return f"as of {m.retrieved_at:%Y-%m-%d %H:%M UTC} ({mins} min ago)"
