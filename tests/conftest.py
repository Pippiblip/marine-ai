"""Pytest configuration."""

import pytest

from orca.guardrails.resilience import reset_breaker, reset_last_ok


@pytest.fixture(autouse=True)
def _fast_retries(monkeypatch):
    """Keep resilience retries instant in tests."""
    monkeypatch.setattr("orca.guardrails.resilience.time.sleep", lambda _s: None)


@pytest.fixture(autouse=True)
def _reset_resilience():
    """Isolate circuit-breaker and last-known cache between tests."""
    reset_breaker()
    reset_last_ok()
    yield
    reset_breaker()
    reset_last_ok()
