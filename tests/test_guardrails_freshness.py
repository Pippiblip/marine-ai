"""Tests for freshness checks and caption generation."""

from datetime import datetime, timedelta, timezone

from orca.guardrails.freshness import caption, is_fresh
from orca.schemas import Measurement, SourceName


def test_is_fresh_true_for_recent_measurement():
    """Recent readings should be considered fresh."""
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    m = Measurement(
        value=2.0,
        unit="m",
        source=SourceName.IMO_MARINE if hasattr(SourceName, "IMO_MARINE") else SourceName.MOCK,
        retrieved_at=now - timedelta(minutes=5),
    )
    assert is_fresh(m, max_age_s=600, now=now)


def test_is_fresh_false_for_old_measurement():
    """Older readings should fail freshness checks."""
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    m = Measurement(
        value=2.0,
        unit="m",
        source=SourceName.MOCK,
        retrieved_at=now - timedelta(hours=2),
    )
    assert not is_fresh(m, max_age_s=600, now=now)


def test_caption_uses_time_and_age():
    """The caption should include the time and age."""
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    m = Measurement(
        value=2.0,
        unit="m",
        source=SourceName.MOCK,
        retrieved_at=now - timedelta(minutes=45),
    )
    text = caption(m, now=now)
    assert "as of" in text
    assert "45 min ago" in text
