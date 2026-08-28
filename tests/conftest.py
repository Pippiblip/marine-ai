"""Pytest configuration."""

import pytest

from orca.guardrails.resilience import reset_breaker, reset_last_ok
from orca.tools.channels.ivr import clear_spoken
from orca.tools.channels.whatsapp import clear_sent


@pytest.fixture(autouse=True)
def _isolate_resilience(monkeypatch):
    """Keep retries instant and breakers/caches isolated per test."""
    monkeypatch.setattr("orca.guardrails.resilience.time.sleep", lambda _s: None)
    reset_breaker()
    reset_last_ok()
    clear_sent()
    clear_spoken()
    yield
    reset_breaker()
    reset_last_ok()
