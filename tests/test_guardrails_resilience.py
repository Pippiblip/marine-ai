"""Retry, backoff, and circuit-breaker tests with no wall-clock waiting."""

from datetime import datetime, timezone

from orca.guardrails.resilience import fetch, reset_breakers
from orca.schemas import SourceName, ToolResponse, ToolStatus

NOW = datetime(2026, 8, 28, 6, 0, tzinfo=timezone.utc)


class ScriptedTool:
    def __init__(self, responses: list[ToolResponse], source: SourceName = SourceName.IMD_MARINE):
        self.responses = responses
        self.source = source
        self.calls = 0

    def __call__(self, request: object) -> ToolResponse:
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return response


def response(
    status: ToolStatus,
    error: str | None = None,
    source: SourceName = SourceName.IMD_MARINE,
) -> ToolResponse:
    return ToolResponse(status=status, source=source, retrieved_at=NOW, error=error)


def test_retry_then_success_records_freshness():
    reset_breakers()
    tool = ScriptedTool([response(ToolStatus.ERROR, "temporary"), response(ToolStatus.OK)])
    sleeps: list[float] = []
    freshness = {}
    result = fetch(tool, None, freshness=freshness, sleep=sleeps.append, clock=lambda: 0.0)
    assert result.status == ToolStatus.OK
    assert tool.calls == 2
    assert sleeps == [0.5]
    assert freshness[SourceName.IMD_MARINE] == NOW


def test_empty_is_not_retried():
    reset_breakers()
    tool = ScriptedTool([response(ToolStatus.EMPTY), response(ToolStatus.OK)])
    result = fetch(tool, None, sleep=lambda _: None, clock=lambda: 0.0)
    assert result.status == ToolStatus.EMPTY
    assert tool.calls == 1


def test_all_attempts_fail_and_breaker_opens_after_three_cycles():
    reset_breakers()
    tool = ScriptedTool([response(ToolStatus.ERROR, "down")])
    now = [0.0]
    for _ in range(3):
        result = fetch(tool, None, sleep=lambda _: None, clock=lambda: now[0])
        assert result.status == ToolStatus.ERROR
    calls_before = tool.calls
    result = fetch(tool, None, sleep=lambda _: None, clock=lambda: now[0])
    assert result.error == "circuit_open"
    assert tool.calls == calls_before

    now[0] = 61.0
    result = fetch(tool, None, sleep=lambda _: None, clock=lambda: now[0])
    assert result.status == ToolStatus.ERROR
    assert tool.calls == calls_before + 3


def test_tool_exception_becomes_error_response():
    reset_breakers()

    class RaisingTool(ScriptedTool):
        def __call__(self, request: object) -> ToolResponse:
            self.calls += 1
            raise RuntimeError("boom")

    result = fetch(RaisingTool([]), None, sleep=lambda _: None, clock=lambda: 0.0)
    assert result.status == ToolStatus.ERROR
    assert "boom" in (result.error or "")


def test_breaker_state_is_isolated_per_source():
    reset_breakers()
    weather = ScriptedTool([response(ToolStatus.ERROR)], SourceName.IMD_MARINE)
    ocean = ScriptedTool(
        [response(ToolStatus.ERROR, source=SourceName.INCOIS_OCEAN_STATE)],
        SourceName.INCOIS_OCEAN_STATE,
    )
    for _ in range(3):
        fetch(weather, None, sleep=lambda _: None, clock=lambda: 0.0)
    result = fetch(ocean, None, sleep=lambda _: None, clock=lambda: 0.0)
    assert result.error != "circuit_open"
    assert ocean.calls == 3
