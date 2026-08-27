# 07 — Testing & the demo

Two things this doc pins down: (1) how the system is tested so it stays trustworthy, and (2) the exact three-moment demo that sells the project. The demo is not an afterthought — it is the acceptance test for the whole MVP, and the tests exist to guarantee the demo behaves.

---

## Part A — Testing strategy

Everything runs **offline, deterministically, with no API keys**. The mock LLM, mock speech, and fixtures make this possible. `pytest -q` from a fresh clone must be green.

### Test layers (build them alongside each milestone, not after)

**Unit — deterministic core (the majority of tests).** `guardrails/` and `geo/` are pure functions; test them exhaustively. These are the tests that actually protect the fisherman.
- `test_guardrails_thresholds.py` — for each rule: just-below → no flag; just-above → flag with correct `code`/`severity`/`message_key`; exactly-at the limit → documented boundary behavior; missing reading → no crash, no flag.
- `test_guardrails_freshness.py` — fresh vs stale on both sides of the safety (30 min) and PFZ (hours) windows; `caption()` string format.
- `test_guardrails_resilience.py` — retry-then-succeed; all-attempts-fail → `ERROR`; breaker opens after N consecutive failures and short-circuits during cooldown; `EMPTY` is never retried. Inject a fake clock/sleep so it's instant.
- `test_guardrails_provenance.py` — clean draft passes; a stray unbacked number fails and is named; sensible rounding is allowed.
- `test_geo_distance.py` / `test_geo_geofence.py` — known lat/lon pairs → known distance & bearing (tolerance-checked); a point clearly inside and one clearly outside the IMBL buffer.

**Component — tools & adapters.** `test_tools_*.py`: each mock returns `OK` + `Measurement`s for a known cell, `EMPTY` for an unknown cell, and `ERROR` via the force-error path; real adapters raise `NotImplementedError`.

**Agent — node behavior.** `test_agents_*.py`: router maps each MVP query to the right `intent` + `subtasks`; weather_risk appends the correct flags for the cyclone fixture and none for the calm one; synthesis emits the failure template when `guardrail_status="failed"` and never a normal answer.

**End-to-end — the whole graph over fixtures.** `test_end_to_end.py` — the three tests that mirror the demo (below). If these pass, the demo works.

### Conventions
- Deterministic clocks: pass `now=` into freshness/guardrail functions; never call `datetime.now()` inside a pure function under test.
- Fixtures via `scripts/seed_fixtures.py`; tests read the same calm/cyclone cells the demo uses, so tests and demo can't drift.
- `pytest-asyncio` for the FastAPI/WS routes. Assert outbound channel calls against the **mock** channel adapters (no network).
- Keep `MockLLM` deterministic (keyword intent classification, template narration) so end-to-end output is stable enough to assert on.

### The verification gate (do this before calling the MVP done)
Run, and eyeball, all three:
```bash
pytest -q                     # all green, offline, no keys
ruff check . && black --check .
python scripts/run_demo.py     # prints the 3 moments identically on repeat runs
```

---

## Part B — The demo (this is the pitch)

Three moments, in order. The first shows capability; the second shows the safety spine; **the third is the one that wins** — it shows the system refusing to lie. `scripts/run_demo.py` runs all three headless; the web client does 1 and 2 live.

### Moment 1 — "Where's the nearest fishing zone?" (capability)
- **Input:** voice/text query over the **calm** cell, with a user location.
- **Path:** `pfz_nearest` → marine_data (PFZ + chlorophyll/SST) → geospatial (nearest node, haversine distance + bearing) → weather_risk (clear) → guardrail `ok` → synthesis.
- **Output:** one spoken sentence naming the nearest zone, its distance and bearing, and the ISRO/INCOIS source **with a timestamp**. e.g. *"The nearest fishing zone is about 12 km to the south-east. Waters there look productive. Source: INCOIS PFZ advisory, as of 06:00 today."*
- **What to point at:** every number in that sentence exists as a `Measurement`; the satellite EO (chlorophyll) is the ISRO story.

### Moment 2 — "Is it safe to go out tomorrow morning?" (deterministic safety)
- **Input:** safety query over the **cyclone** cell (fixture values above threshold).
- **Path:** `safety_check` → weather_risk retrieves wind/wave/cyclone, `thresholds.evaluate()` appends a **DANGER** flag → guardrail validates the flag against fresh readings → synthesis is forced onto the no-go template.
- **Output:** an unmistakable *"Do not go out,"* naming the tripped number and its time, in the user's language. e.g. *"Do not go out. Wave height is 3.4 m as of 05:30, above the safe limit of 2.5 m. A cyclone is 180 km away. Stay ashore."*
- **What to point at:** the verdict came from Python, not the model. Say to the judges: *"I can change the model's wording, but I cannot make it say 'safe' here — the threshold is hard-coded and unit-tested."* Optionally show `test_guardrails_thresholds.py` going green.

### Moment 3 — Kill a data source, re-ask (the trust moment — lead with this in Q&A)
- **Input:** re-ask the safety question, but first **kill the weather source** (point the tool at a missing fixture or flip its force-error flag).
- **Path:** `fetch()` retries, exhausts, trips the breaker → `ToolResponse(status=ERROR)` → guardrail sets `guardrail_status="failed"` → synthesis emits the `data_unavailable` template (and the last-known reading *with its age* if one exists).
- **Output:** *"I can't get current weather data right now. I won't guess about your safety. My last reading was 3.4 m at 05:30, which may be out of date — follow local warnings."*
- **What to point at:** this is the entire thesis. A typical chatbot hallucinates a confident answer here; ORCA **says it doesn't know**, explains why, and hands over the only honest thing it has (a timestamped last-known value). *"Wrong-but-confident can get someone killed. This is the difference."*

### Demo staging notes
- Pre-seed both cells with `scripts/seed_fixtures.py` so runs are identical.
- Keep everything on mocks for the live demo — no network means no demo-day surprises. Mention that real INCOIS/IMD/ISRO adapters are stubbed behind the same interface (`docs/04 §6`), so "productionizing is wiring, not redesign."
- If asked "why multi-agent?", give the three reasons from `docs/01 §2` (safety separation, source attribution, parallelism) — and note that the killed-source behavior only stays contained because retries/breaker live in one guardrail module, not sprinkled across agents.
- Have `pytest -q` green in a terminal tab. For a safety-critical system, "the tests pass" *is* part of the pitch.
