"""Retry and circuit-breaker policy for source tool calls."""

import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Protocol

from orca.schemas import SourceName, ToolResponse, ToolStatus

MAX_ATTEMPTS = 3
BACKOFF_S = (0.0, 0.5, 1.5)
BREAKER_THRESHOLD = 3
BREAKER_COOLDOWN_S = 60.0


class Tool(Protocol):
    """Minimum interface required by the resilience wrapper."""

    source: SourceName

    def __call__(self, request: Any) -> ToolResponse:
        """Perform one adapter attempt."""


_breaker: dict[SourceName, dict[str, float]] = {}


def _breaker_open(source: SourceName, now: float) -> bool:
    state = _breaker.get(source)
    return bool(state and state["open_until"] > now)


def reset_breakers() -> None:
    """Clear breaker state, primarily for isolated tests and process startup."""

    _breaker.clear()


def fetch(
    tool: Tool,
    request: Any,
    *,
    freshness: dict[SourceName, datetime] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> ToolResponse:
    """Call a tool with retries and a per-source circuit breaker.

    Adapter exceptions are converted to ``ERROR`` responses. ``EMPTY`` is a
    valid result and therefore returns immediately without consuming retries.
    """

    source = tool.source
    if _breaker_open(source, clock()):
        return ToolResponse(
            status=ToolStatus.ERROR,
            source=source,
            retrieved_at=wall_clock(),
            error="circuit_open",
        )

    last_response: ToolResponse | None = None
    for attempt in range(MAX_ATTEMPTS):
        delay = BACKOFF_S[attempt]
        if delay:
            sleep(delay)
        try:
            response = tool(request)
        except Exception as exc:  # adapters must not leak failures to agents
            response = ToolResponse(
                status=ToolStatus.ERROR,
                source=source,
                retrieved_at=wall_clock(),
                error=repr(exc),
            )
        last_response = response

        if response.status == ToolStatus.OK:
            _breaker[source] = {"fails": 0.0, "open_until": 0.0}
            if freshness is not None:
                freshness[source] = response.retrieved_at
            return response
        if response.status == ToolStatus.EMPTY:
            return response

    state = _breaker.setdefault(source, {"fails": 0.0, "open_until": 0.0})
    state["fails"] += 1
    if state["fails"] >= BREAKER_THRESHOLD:
        state["open_until"] = clock() + BREAKER_COOLDOWN_S
    assert last_response is not None
    return last_response
