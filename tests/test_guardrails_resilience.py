"""Tests for tool resilience with retries and circuit breaker behavior."""

from datetime import datetime, timezone

from orca.guardrails.resilience import fetch, reset_breaker
from orca.schemas import SourceName, ToolResponse, ToolStatus


class FlakyTool:
    """Tool stub that fails a set number of times before succeeding."""

    def __init__(self, fails_before_success: int = 0):
        self.calls = 0
        self.fails_before_success = fails_before_success

    def __call__(self, request):
        """Execute a call and fail before success if configured."""
        self.calls += 1
        if self.calls <= self.fails_before_success:
            raise RuntimeError("temporary failure")
        return ToolResponse(
            status=ToolStatus.OK,
            source=SourceName.MOCK,
            retrieved_at=datetime.now(timezone.utc),
            payload={"ok": True},
        )


def test_retry_then_succeed():
    """Retries should succeed after transient tool failures."""
    reset_breaker(SourceName.MOCK)
    tool = FlakyTool(fails_before_success=2)
    resp = fetch(tool, {}, SourceName.MOCK)
    assert resp.status == ToolStatus.OK
    assert tool.calls == 3


def test_all_fail_returns_error():
    """Persistent failures should ultimately return an error response."""
    reset_breaker(SourceName.MOCK)

    def failing_tool(_request):
        raise RuntimeError("still broken")

    resp = fetch(failing_tool, {}, SourceName.MOCK)
    assert resp.status == ToolStatus.ERROR


def test_empty_is_not_retried():
    """Empty responses are valid and should not be retried."""
    reset_breaker(SourceName.MOCK)

    def empty_tool(_request):
        return ToolResponse(
            status=ToolStatus.EMPTY,
            source=SourceName.MOCK,
            retrieved_at=datetime.now(timezone.utc),
            payload=None,
        )

    resp = fetch(empty_tool, {}, SourceName.MOCK)
    assert resp.status == ToolStatus.EMPTY


def test_breaker_trips_after_consecutive_failures():
    """Circuit breaker should open after repeated failures."""
    reset_breaker(SourceName.MOCK)

    def always_fail(_request):
        raise RuntimeError("nope")

    for _ in range(3):
        fetch(always_fail, {}, SourceName.MOCK)

    resp = fetch(always_fail, {}, SourceName.MOCK)
    assert resp.status == ToolStatus.ERROR
    assert "circuit_breaker_open" in (resp.error or "")
