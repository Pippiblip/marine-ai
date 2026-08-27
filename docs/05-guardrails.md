# 05 — The guardrail layer (build this best)

This is the differentiator. Everything else is plumbing; **this** is why a fisherman can trust the answer with their life. It is 100% deterministic Python — no LLM anywhere in this package — and it is the most heavily unit-tested part of the codebase. Five modules under `src/orca/guardrails/`.

Golden framing: **the LLM is allowed to choose words; the guardrail decides truth.** If these two ever disagree, the guardrail wins and the LLM's output is discarded.

---

## 1. `thresholds.py` — safety verdicts (hard-coded)

The single source of go/no-go truth. Defaults live in code; env may override for demo staging but a default always exists without any env.

```python
# src/orca/guardrails/thresholds.py
from orca.config import settings
from orca.schemas import (WeatherRiskResult, SafetyFlag, Severity, Measurement)

# SAFETY: these constants are the whole ballgame. Change only with review.
WAVE_UNSAFE_M   = settings.wave_unsafe_m      # default 2.5
WIND_UNSAFE_KT  = settings.wind_unsafe_kt      # default 25
CYCLONE_NEAR_KM = settings.cyclone_near_km     # default 300
SWELL_UNSAFE_M  = settings.swell_unsafe_m      # default 2.0

def evaluate(wr: WeatherRiskResult) -> list[SafetyFlag]:
    """Pure function: readings in, flags out. No I/O, no LLM, fully unit-tested."""
    flags: list[SafetyFlag] = []

    def flag(code, sev, key, m: Measurement, rule: str):
        flags.append(SafetyFlag(code=code, severity=sev, message_key=key,
                                triggered_by=[m], threshold_repr=rule))

    # SAFETY: wave height
    if wr.wave_height and wr.wave_height.value > WAVE_UNSAFE_M:
        flag("high_wave", Severity.DANGER, "danger_high_wave",
             wr.wave_height, f"wave_height > {WAVE_UNSAFE_M} m")
    # SAFETY: wind speed
    if wr.wind_speed and wr.wind_speed.value > WIND_UNSAFE_KT:
        flag("high_wind", Severity.DANGER, "danger_high_wind",
             wr.wind_speed, f"wind_speed > {WIND_UNSAFE_KT} kt")
    # SAFETY: cyclone proximity
    if wr.cyclone_distance and wr.cyclone_distance.value < CYCLONE_NEAR_KM:
        flag("cyclone_proximity", Severity.DANGER, "danger_cyclone",
             wr.cyclone_distance, f"cyclone_distance < {CYCLONE_NEAR_KM} km")
    # SAFETY: swell surge
    if wr.swell_surge and wr.swell_surge.value > SWELL_UNSAFE_M:
        flag("swell_surge", Severity.WARNING, "warn_swell",
             wr.swell_surge, f"swell_surge > {SWELL_UNSAFE_M} m")
    return flags
```

Rules:
- **Only the Weather & Risk agent calls `evaluate()`**, and it is the only writer of `safety_flags`.
- A `DANGER` flag means the final answer's verdict is **no-go**, full stop. The LLM narrates it; it cannot overturn or hedge it.
- Every constant used in a comparison is named and mirrored in `.env.example`. No magic numbers inline.
- Comparisons are strict/explicit and match `threshold_repr` exactly so the spoken rule and the code agree.

---

## 2. `freshness.py` — staleness & timestamps

Old data is a lie told with a straight face. This module decides whether a reading is fresh enough to use, and how to caption its age.

```python
# src/orca/guardrails/freshness.py
from datetime import datetime, timezone
from orca.config import settings
from orca.schemas import Measurement, SourceName

SAFETY_MAX_AGE_S = settings.freshness_max_min_safety * 60     # default 30 min
PFZ_MAX_AGE_S    = settings.freshness_max_hours_pfz * 3600    # default 6 h

def is_fresh(m: Measurement, *, max_age_s: int, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    return m.age_seconds(now) <= max_age_s

def caption(m: Measurement, now: datetime | None = None) -> str:
    """Human 'as of' string for citations. Never silently drops the time."""
    now = now or datetime.now(timezone.utc)
    mins = int(m.age_seconds(now) // 60)
    return f"as of {m.retrieved_at:%Y-%m-%d %H:%M UTC} ({mins} min ago)"
```

- Safety-relevant readings (wave/wind/cyclone) use the **tight** window (`SAFETY_MAX_AGE_S`, 30 min). PFZ advisories use the **loose** window (hours) — a fishing zone doesn't move minute to minute.
- If a safety reading is **stale**, that is *not* "safe." It routes to `guardrail_status="stale"` → caution template with the explicit age, or to `"failed"` if there's nothing usable.
- Freshness is always *reported*, even when fresh (`caption()` feeds the citation). The user always hears when the data is from.

---

## 3. `resilience.py` — retries, backoff, circuit breaker

Wraps every tool call. This is the `fetch()` that agents actually use (see `docs/04 §4`). Tools attempt once; **this** owns policy.

```python
# src/orca/guardrails/resilience.py
import time
from datetime import datetime, timezone
from orca.schemas import ToolResponse, ToolStatus, SourceName

MAX_ATTEMPTS = 3
BACKOFF_S = [0.0, 0.5, 1.5]          # attempt 1 immediate, then backoff
BREAKER_THRESHOLD = 3                 # consecutive failures → open
BREAKER_COOLDOWN_S = 60

_breaker: dict[SourceName, dict] = {}   # source -> {"fails": int, "open_until": float}

def _breaker_open(src: SourceName, now: float) -> bool:
    st = _breaker.get(src)
    return bool(st and st["open_until"] > now)

def fetch(tool, req, *, freshness: dict | None = None) -> ToolResponse:
    """Retry with backoff; trip a per-source breaker; NEVER raise into the agent."""
    now = time.monotonic()
    if _breaker_open(tool.source, now):
        return ToolResponse(status=ToolStatus.ERROR, source=tool.source,
                            retrieved_at=datetime.now(timezone.utc),
                            payload=None, error="circuit_open")
    last = None
    for attempt in range(MAX_ATTEMPTS):
        time.sleep(BACKOFF_S[attempt])
        try:
            resp = tool(req)
        except Exception as e:                    # defensive; tools shouldn't raise
            resp = ToolResponse(status=ToolStatus.ERROR, source=tool.source,
                                retrieved_at=datetime.now(timezone.utc),
                                payload=None, error=repr(e))
        last = resp
        if resp.status == ToolStatus.OK:
            _breaker[tool.source] = {"fails": 0, "open_until": 0.0}
            if freshness is not None:             # record success time for staleness checks
                freshness[tool.source] = resp.retrieved_at
            return resp
        # EMPTY is a valid answer (no data for area/time) — don't retry it
        if resp.status == ToolStatus.EMPTY:
            return resp
    # exhausted → count toward breaker
    st = _breaker.setdefault(tool.source, {"fails": 0, "open_until": 0.0})
    st["fails"] += 1
    if st["fails"] >= BREAKER_THRESHOLD:
        st["open_until"] = time.monotonic() + BREAKER_COOLDOWN_S
    return last
```

- **Retry** only transient `ERROR`; never retry `EMPTY` (that's a real answer).
- **Circuit breaker** per source: after N consecutive failed cycles, short-circuit for a cooldown so a dead source doesn't stall every request. This is what makes the "kill a source" demo degrade gracefully instead of hanging.
- On success it records `data_freshness[source]`. On exhaustion it returns the last `ERROR` response — the agent/guardrail then decides between cached-last-known and explicit failure.
- Uses `time.monotonic()` for breaker timing; wall-clock (`datetime`) only for `retrieved_at`. In tests, inject a fake clock/sleep so retries are instant.

---

## 4. `provenance.py` — every number in the answer must exist in the data

The anti-hallucination check. After Synthesis drafts text but **before** it is spoken, verify that every number in the draft traces to a real `Measurement` in state.

```python
# src/orca/guardrails/provenance.py
import re
from orca.schemas import Measurement

_NUM = re.compile(r"\d+(?:\.\d+)?")

def collect_allowed(measurements: list[Measurement]) -> set[str]:
    allowed = set()
    for m in measurements:
        allowed.add(f"{m.value:g}")
        allowed.add(f"{round(m.value)}")          # allow sensible rounding in speech
    return allowed

def verify(draft: str, measurements: list[Measurement]) -> tuple[bool, list[str]]:
    """Return (ok, offending_numbers). A number in the draft not backed by a
    Measurement is a provenance violation → draft is rejected."""
    allowed = collect_allowed(measurements)
    # ignore obviously-safe tokens (dates/times handled separately via citations)
    offending = [tok for tok in _NUM.findall(draft) if tok not in allowed]
    return (len(offending) == 0, offending)
```

- Synthesis passes its draft plus the flat list of every `Measurement` in state. If `verify` fails, the draft is **rejected** and Synthesis must regenerate constrained to the facts, or fall back to a template. It must never speak an unverifiable number.
- Keep an allowlist for legitimately non-data numbers if needed (e.g., "top 3 zones") — but prefer templates that avoid stray numerals. Document any allowlist entry with a comment.
- This check is deliberately strict and dumb. Strict-and-dumb is auditable; clever is not.

---

## 5. `templates.py` — explicit-failure & disclaimer language

When data is missing, stale, or a source is down, the system **says so** in the user's language — it never guesses and never goes silent. These are fixed templates keyed by `message_key`, filled only with values that came from data.

```python
# src/orca/guardrails/templates.py
TEMPLATES = {
    # safety verdicts (filled from SafetyFlag.triggered_by + freshness.caption)
    "danger_high_wave": "Do not go out. Wave height is {value} m ({caption}), above the safe limit of {limit} m.",
    "danger_high_wind": "Do not go out. Wind is {value} kt ({caption}), above the safe limit of {limit} kt.",
    "danger_cyclone":   "Do not go out. A cyclone is {value} km away ({caption}). Stay ashore and follow local warnings.",
    "warn_swell":       "Caution: swell surge is {value} m ({caption}). Small boats should avoid going out.",
    "all_clear":        "Conditions look safe right now: waves {wave} m, wind {wind} kt ({caption}). Always stay alert.",

    # failure / staleness (the trust-defining messages)
    "data_unavailable": "I can't get current {what} data right now. I won't guess about your safety. Please try again shortly or follow local warnings.",
    "data_stale":       "Warning: my most recent {what} reading is from {caption}, which may be out of date. Do not rely on it — check local sources before going out.",
    "partial_data":     "I could get {have} but not {missing}. Based only on what I have: {summary}. Treat this as incomplete.",
    "location_unknown": "I need your location to answer that. Please share it or tell me your landing centre.",
}
```

- Templates are **English source strings**; the Speech layer translates to `source_lang`. Keep them short, literal, and imperative — they may be heard over a bad phone line.
- The failure templates are the point of the whole project. `docs/07`'s third demo moment is literally triggering `data_unavailable`. Make it land: no invented reading, an explicit "I won't guess about your safety," and the last-known value *with its time* if one exists.

---

## 6. The guardrail node (how it runs in the graph)

`src/orca/agents/` has no separate file for this — the guardrail runs as a graph node wired in `graph.py`, calling into these five modules in order. Its job each request:

1. **Collect** every `Measurement` and `SafetyFlag` from the specialist results in state.
2. **Freshness**: for each safety-relevant reading, check `is_fresh(..., SAFETY_MAX_AGE_S)`. Any stale critical reading → `guardrail_status="stale"` (or `"failed"` if nothing usable), and note it.
3. **Validate flags**: confirm each `SafetyFlag.triggered_by` reading is present and fresh; the guardrail may drop a flag built on stale data (re-routing to a staleness message) but may **never invent** a flag.
4. **Decide status**: `ok` (fresh + complete), `stale` (usable but old → caution template), or `failed` (missing/erroring critical source → failure template).
5. **Write** `guardrail_status` + `guardrail_notes` (machine-readable reasons + which `message_key` to use). Synthesis reads these and cannot proceed to a normal answer if status ≠ `ok`.

Then, **after** Synthesis drafts, provenance runs on the draft (step 4 above) as the final gate before TTS.

Order of authority, always: **freshness → thresholds → provenance → template fallback.** Truth first, words last.

---

## 7. Tests are part of the deliverable (see `docs/07`)

Because this layer is pure, it is exhaustively unit-tested offline. Mandatory files:
- `tests/test_guardrails_thresholds.py` — each threshold: just-below (no flag), just-above (flag), exactly-at (documented boundary), missing reading (no crash, no flag).
- `tests/test_guardrails_freshness.py` — fresh/stale either side of both windows; caption format.
- `tests/test_guardrails_resilience.py` — retry-then-succeed; all-fail→ERROR; breaker opens after N and cools down; EMPTY not retried (use a fake clock).
- `tests/test_guardrails_provenance.py` — clean draft passes; a stray number fails and names the offender; rounding allowed.

If these tests are green, the demo's scary moments are guaranteed to behave. That guarantee *is* the product.
