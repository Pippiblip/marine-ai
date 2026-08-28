"""Guardrail to verify that every number in a draft is backed by a Measurement."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from orca.schemas import Measurement

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def collect_allowed(
    measurements: list[Measurement],
    *,
    now: datetime | None = None,
    extra: set[str] | None = None,
) -> set[str]:
    """
    Return all numeric strings that are allowed to appear in a draft.

    This is intentionally conservative: if a value is present in state as a
    Measurement, it may be spoken either exactly or in a rounded form.
    Timestamp parts and age-in-minutes from ``caption()`` are also allowed.

    Args:
        measurements: The list of source-backed measurements.
        now: Clock used for age captions.
        extra: Additional allowed numeric tokens (e.g. hard-coded thresholds).

    Returns:
        Set of allowed numeric strings.

    """
    allowed: set[str] = set(extra or ())
    now = now or datetime.now(timezone.utc)
    for m in measurements:
        allowed.add(f"{m.value:g}")
        allowed.add(f"{m.value:.1f}")
        allowed.add(f"{m.value:.0f}")
        allowed.add(f"{round(m.value)}")
        dt = m.retrieved_at
        allowed.add(str(dt.year))
        allowed.add(str(dt.month))
        allowed.add(f"{dt.month:02d}")
        allowed.add(str(dt.day))
        allowed.add(f"{dt.day:02d}")
        allowed.add(str(dt.hour))
        allowed.add(f"{dt.hour:02d}")
        allowed.add(str(dt.minute))
        allowed.add(f"{dt.minute:02d}")
        allowed.add(str(int(m.age_seconds(now) // 60)))
        if m.observed_at is not None:
            obs = m.observed_at
            allowed.add(str(obs.year))
            allowed.add(f"{obs.month:02d}")
            allowed.add(f"{obs.day:02d}")
            allowed.add(f"{obs.hour:02d}")
            allowed.add(f"{obs.minute:02d}")
    return allowed


def verify(
    draft: str,
    measurements: list[Measurement],
    *,
    extra_allowed: set[str] | None = None,
    now: datetime | None = None,
) -> tuple[bool, list[str]]:
    """
    Verify that the draft contains no unbacked numeric values.

    Args:
        draft: Candidate response draft.
        measurements: Measurements that may be cited.
        extra_allowed: Extra numeric tokens (thresholds).
        now: Clock used for age captions.

    Returns:
        Tuple[bool, list[str]]: (is_valid, offending_numbers).

    """
    allowed = collect_allowed(measurements, now=now, extra=extra_allowed)
    offending = [tok for tok in _NUM_RE.findall(draft) if tok not in allowed]
    return (len(offending) == 0, offending)
