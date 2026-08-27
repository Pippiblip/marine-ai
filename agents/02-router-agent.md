# Agent 02 — Router & Planning

> File: `src/orca/agents/router.py` · Node: `router` · **Always runs.** MVP: build fully.

## Job
Decide *what kind of question* this is and *which specialists* must run. This is the only place intent is classified, and it's the one legitimate LLM classification call in the pipeline. It plans; it does not fetch or reason about data.

## State I/O
**Writes:** `intent`, `subtasks` (list of specialist node names).
**Reads:** `query_text`, `user_location`, `channel`.

## Tools / dependencies
- `llm` interface `classify(text, labels)` via `get_llm()` — default `MockLLM` (keyword-based). **Deterministic prompt, temperature 0.**
- No data tools.

## Algorithm
1. `intent = llm.classify(query_text, labels=["pfz_nearest","safety_check","boundary_check","conditions_summary"])`.
   - `MockLLM` maps keywords: "fish/zone/catch" → `pfz_nearest`; "safe/go out/weather/storm/cyclone" → `safety_check`; "border/boundary/line" → `boundary_check`; else best-effort → `conditions_summary`.
2. Map intent → `subtasks` per `docs/01 §3`:
   - `pfz_nearest` → `["marine_data","geospatial","weather_risk"]` (weather included so the answer can add a safety note on the chosen zone).
   - `safety_check` → `["weather_risk","geospatial"]`.
   - `boundary_check` *(scaffold)* → `["geospatial"]`.
   - `conditions_summary` *(scaffold)* → `["weather_risk"]`.
3. If `user_location is None` and the intent needs it, still set subtasks but let the guardrail/synthesis raise `location_unknown` (don't guess a location).

## Guardrail interactions
- None directly. But the router must **never** widen scope beyond the mapping (no calling all agents "just in case") — parallelism and traceability depend on a tight subtask list.
- The LLM here chooses a **label from a fixed set** only. It cannot emit free text that becomes an instruction downstream.

## Acceptance test
`test_agents_router.py`: each of the two MVP queries maps to the exact `intent` and `subtasks` above; an out-of-scope query still returns a valid label (no crash); classification is deterministic under `MockLLM`.
