"""Tests for provenance validation of drafted responses."""

from datetime import datetime, timezone

from orca.guardrails.provenance import verify
from orca.schemas import Measurement, SourceName


def test_provenance_clean_draft_passes():
    """A draft that matches known measurements should pass."""
    measurements = [
        Measurement(
            value=2.4,
            unit="m",
            source=SourceName.MOCK,
            retrieved_at=datetime(2026, 9, 20, 6, 0, tzinfo=timezone.utc),
        )
    ]
    ok, offending = verify("Wave height is 2.4 m.", measurements)
    assert ok is True
    assert offending == []


def test_provenance_unbacked_number_fails():
    """Numbers not in state should be rejected."""
    measurements = [
        Measurement(
            value=2.4,
            unit="m",
            source=SourceName.MOCK,
            retrieved_at=datetime(2026, 9, 20, 6, 0, tzinfo=timezone.utc),
        )
    ]
    ok, offending = verify("Wave height is 2.4 m and 9.1 m.", measurements)
    assert ok is False
    assert "9.1" in offending


def test_provenance_rounding_allowed():
    """Rounded values derived from a measurement should be accepted."""
    measurements = [
        Measurement(
            value=2.49,
            unit="m",
            source=SourceName.MOCK,
            retrieved_at=datetime(2026, 9, 20, 6, 0, tzinfo=timezone.utc),
        )
    ]
    ok, offending = verify("Wave height is 2 m.", measurements)
    assert ok is True
    assert offending == []
