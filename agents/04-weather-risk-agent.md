# Agent 04 — Weather & Risk

> File: `src/orca/agents/weather_risk.py` · Node: `weather_risk` · MVP: build fully. **The only agent that may raise a `SafetyFlag`.** Runs for `safety_check` and `pfz_nearest`.

## Job
Retrieve weather/ocean-state/cyclone data for the user's area and apply the **hard-coded safety thresholds**. This agent owns the safety verdict inputs. It is deliberately the only writer of `safety_flags`, so the safety path is auditable in one place.

## State I/O
**Writes:** `weather_risk_result: WeatherRiskResult` (wave/wind/cyclone/swell as `Measurement`s + `safety_flags`), and **appends** to `state["safety_flags"]`.
**Reads:** `user_location`, `intent`.

## Tools / dependencies
- `imd_get_marine_warnings` → `MarineWarningPayload` (wind, wave, cyclone distance, CAP fields).
- `incois_get_ocean_state` → `OceanStatePayload` (wave height, swell surge, SST).
- `guardrails/thresholds.py::evaluate` — the hard-coded rules. **This agent does not define thresholds itself; it calls `evaluate()`.**
- All fetches via `resilience.fetch(..., freshness=state["data_freshness"])`.

## Algorithm
1. Build the `BoundingBox` for `user_location`.
2. `fetch` IMD warnings and INCOIS ocean-state; map values into `Measurement`s (correct units: wind `kt`, wave `m`, cyclone `km`, swell `m`), carrying `retrieved_at` (and `observed_at` where the payload has it).
3. Assemble `WeatherRiskResult`.
4. `flags = thresholds.evaluate(result)` — pure function. Set `result.safety_flags = flags` and append them to `state["safety_flags"]`.
5. Record `source_freshness` for each `OK` source.

## Guardrail interactions
- Produces the `SafetyFlag`s the guardrail then **validates against freshness** (a flag built on a stale reading may be downgraded to a staleness message by the guardrail — but the guardrail never invents a flag).
- Carries `cap_severity` for context only; **our** verdict is `evaluate()`'s output, never the source's severity string.
- On tool `ERROR` for a safety-critical source, write no reading for it. Missing critical data is the guardrail's cue for `failed`/`stale` — this agent must not substitute a guess or a default "calm."

## Acceptance test
`test_agents_weather_risk.py`: cyclone cell → readings above limits → a `DANGER` `high_wave` (and/or `cyclone_proximity`) flag whose `triggered_by` holds the exact `Measurement`; calm cell → no flags; missing IMD source → no reading, no flag, no crash.
