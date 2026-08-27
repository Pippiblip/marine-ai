# Agent 07 — Ocean Analytics *(SCAFFOLD / v2 — do NOT fully build)*

> File: `src/orca/agents/ocean_analytics.py` · Node: `ocean_analytics` (exists, not on the MVP graph path) · **Scaffold only.**

## Why this is scaffold
Historical/trend analysis ("why did the catch drop near here this season?") is the heaviest pipeline (Copernicus reanalysis, NetCDF via xarray, multi-month subsetting) and the **least** demo value per hour of work. Building it would blow the MVP scope. So: create the file, the node, and the result type — leave the body a `# TODO(orca):`. Present, not completed, not deleted.

## Intended job (for the TODO author)
Given a location and a time window, retrieve historical ocean variables (chlorophyll, SST, currents) from Copernicus and surface **observations** — never invented causation. e.g. "chlorophyll here is lower than the 5-year average for this month," stated as an observation with its source and period.

## State I/O (define the type now, stub the writer)
**Writes:** `ocean_analytics_result: OceanAnalyticsResult` (`observation: str | None`, `series: list[Measurement]`).
**Reads:** `user_location`, and a time window (future intent `conditions_history`).

## Tools / dependencies
- `tools/copernicus.py` (scaffold) — NetCDF subset via xarray. `# TODO(orca): open granule, subset bbox/time, extract series.`
- May use `llm.narrate` **only** to phrase already-computed observations — same rule as everyone: no invented numbers, no invented causation.

## Scaffold body (what to actually write in M-later)
```python
def ocean_analytics(state: PlatformState) -> PlatformState:
    # TODO(orca): v2 — Copernicus/NetCDF trend analysis.
    # For now, no-op so the node is graph-safe if ever routed.
    state["ocean_analytics_result"] = OceanAnalyticsResult(observation=None, series=[])
    return state
```

## Guardrail interactions
- Same rules apply when built: every number a `Measurement`; observations only, never causal claims from the LLM; provenance still gates any output that reaches the user.

## Acceptance test (scaffold-level only)
`test_agents_ocean_analytics.py`: importing and calling the node returns a valid empty `OceanAnalyticsResult` without error, and it is **not** reached by the two MVP intents' subtask lists.
