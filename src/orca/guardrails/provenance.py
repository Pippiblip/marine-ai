"""Strict checks that spoken numbers came from retrieved measurements."""

import re

from orca.schemas import Measurement

_NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![A-Za-z])")
_DATE_OR_TIME = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}:\d{2}(?:\s*(?:AM|PM))?\b",
    re.IGNORECASE,
)


def collect_allowed(measurements: list[Measurement]) -> set[str]:
    """Return canonical and sensibly rounded forms of measurement values."""

    allowed: set[str] = set()
    for measurement in measurements:
        allowed.add(f"{measurement.value:g}")
        allowed.add(str(round(measurement.value)))
    return allowed


def verify(draft: str, measurements: list[Measurement]) -> tuple[bool, list[str]]:
    """Return whether every data number in ``draft`` is provenance-backed.

    ISO dates and clock times belong to citation metadata and are excluded
    from the measurement comparison. All other numeric tokens must be backed
    by a measurement or the draft is rejected.
    """

    allowed = collect_allowed(measurements)
    metadata_spans = [match.span() for match in _DATE_OR_TIME.finditer(draft)]
    offending: list[str] = []
    for match in _NUMBER.finditer(draft):
        if any(start <= match.start() < end for start, end in metadata_spans):
            continue
        token = match.group()
        if token not in allowed:
            offending.append(token)
    return not offending, offending
