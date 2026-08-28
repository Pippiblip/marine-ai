"""Resilience layer: retries, backoff, and circuit breaker for tool calls."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable

from orca.schemas import SourceName, ToolResponse, ToolStatus

# Resilience configuration (can be tuned via env or constants)
MAX_ATTEMPTS = 3
BACKOFF_S = [0.0, 0.5, 1.5]  # immediate, then 0.5s, then 1.5s
BREAKER_THRESHOLD = 3  # consecutive failures to trip
BREAKER_COOLDOWN_S = 60  # seconds to stay open

# Per-source circuit breaker state: {source -> {"fails": int, "open_until": float}}
_breaker_state: dict[SourceName, dict[str, Any]] = {}
# Last successful OK response per source (for explicit-failure last-known).
_last_ok: dict[SourceName, ToolResponse] = {}


def _breaker_is_open(source: SourceName, now: float) -> bool:
    """Check if the breaker is open (tripped) for this source."""
    state = _breaker_state.get(source)
    return bool(state and state["open_until"] > now)


def reset_breaker(source: SourceName = None) -> None:
    """
    Reset the circuit breaker for a source, or all sources if None.

    Useful for testing or recovery. In production, breakers self-cool after cooldown.

    Args:
        source: Source to reset, or None to reset all.

    """
    global _breaker_state
    if source is None:
        _breaker_state.clear()
    elif source in _breaker_state:
        del _breaker_state[source]


def get_last_ok(source: SourceName) -> ToolResponse | None:
    """Return the last successful ToolResponse for a source, if any."""
    return _last_ok.get(source)


def reset_last_ok(source: SourceName | None = None) -> None:
    """Clear cached last-known readings (tests)."""
    if source is None:
        _last_ok.clear()
    else:
        _last_ok.pop(source, None)


def fetch(
    tool_fn: Callable[[Any], ToolResponse],
    request: Any,
    source: SourceName,
    *,
    freshness_dict: dict[SourceName, datetime] = None,
) -> ToolResponse:
    """
    Call a tool with retry, backoff, and circuit breaker protection.

    Never raises an exception — always returns a ToolResponse. Respects
    circuit breaker state: if open, returns ERROR immediately without calling tool.
    Retries transient ERROR responses with backoff. Does NOT retry EMPTY (that is
    a valid result). Records successful fetch times in freshness_dict for staleness checks.

    Args:
        tool_fn: Callable that takes request and returns ToolResponse.
        request: The tool request object.
        source: The SourceName this tool belongs to (for circuit breaker tracking).
        freshness_dict: Optional dict to record {source -> retrieved_at} on success.

    Returns:
        ToolResponse with status OK, EMPTY, or ERROR.

    """
    now = time.monotonic()

    # Check breaker state
    if _breaker_is_open(source, now):
        return ToolResponse(
            status=ToolStatus.ERROR,
            source=source,
            retrieved_at=datetime.now(timezone.utc),
            payload=None,
            error="circuit_breaker_open",
        )

    last_response = None

    for attempt in range(MAX_ATTEMPTS):
        # Backoff before attempt (0.0 for first, then increasing)
        if attempt > 0:
            time.sleep(BACKOFF_S[attempt])

        try:
            response = tool_fn(request)
        except Exception as e:
            # Tool raised unexpectedly; defensive wrapping
            response = ToolResponse(
                status=ToolStatus.ERROR,
                source=source,
                retrieved_at=datetime.now(timezone.utc),
                payload=None,
                error=f"exception: {type(e).__name__}: {str(e)}",
            )

        last_response = response

        # Success: reset breaker and record freshness
        if response.status == ToolStatus.OK:
            _breaker_state[source] = {"fails": 0, "open_until": 0.0}
            _last_ok[source] = response
            if freshness_dict is not None:
                freshness_dict[source] = response.retrieved_at
            return response

        # EMPTY is a valid answer (no data for this query) — don't retry
        if response.status == ToolStatus.EMPTY:
            _breaker_state[source] = {"fails": 0, "open_until": 0.0}
            if freshness_dict is not None:
                freshness_dict[source] = response.retrieved_at
            return response

        # ERROR: continue to next attempt

    # Exhausted all attempts: count toward breaker
    state = _breaker_state.setdefault(source, {"fails": 0, "open_until": 0.0})
    state["fails"] += 1

    if state["fails"] >= BREAKER_THRESHOLD:
        state["open_until"] = time.monotonic() + BREAKER_COOLDOWN_S

    return last_response or ToolResponse(
        status=ToolStatus.ERROR,
        source=source,
        retrieved_at=datetime.now(timezone.utc),
        payload=None,
        error="max_attempts_exceeded",
    )
