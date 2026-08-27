# 06 — Build plan (milestones)

Build in this order. **Do not start a milestone until the previous one's acceptance test passes.** Each milestone is a vertical, testable slice. The guiding principle: the system should *run end-to-end on mocks as early as possible* (by M4), then get hardened. Every milestone leaves the repo green (`pytest -q` passes, `ruff`/`black` clean).

Legend: 🎯 goal · 📁 files · ✅ acceptance test (must pass to advance).

---

## M0 — Skeleton & config
🎯 An installable package that boots with zero keys/network.
📁 `pyproject.toml`, `src/orca/__init__.py`, `config.py` (pydantic-settings + all env from `docs/02 §4`), `logging.py` (structured + `trace_id`), `.env.example`, `README.md` (setup/run/test), `api/app.py` with `GET /health`.
✅ `pip install -e ".[dev]"` succeeds; `uvicorn orca.api.app:app` serves `/health → {"status":"ok"}`; `pytest -q` runs (even if ~empty); `ruff check .` clean.

## M1 — Contracts & provider interfaces
🎯 All shared types and the two AI interfaces exist, with mock impls — no agents yet.
📁 `schemas.py` (every model in `docs/03`), `state.py` (`PlatformState`), `llm/base.py` + `llm/mock.py` + `llm/factory.py` (+ empty `claude.py`/`openai.py` classes raising `NotImplementedError`), `speech/base.py` + `speech/mock.py` (+ `bhashini.py` stub).
✅ `tests/test_contracts.py`: models validate/reject correctly; `Measurement.age_seconds` works. `get_llm()` returns `MockLLM` when `ORCA_LLM_PROVIDER=mock`; `MockLLM.classify` returns a label from the given set; `MockSpeech.asr` returns a fixture transcript. All offline.

## M2 — Deterministic core: geo + guardrails
🎯 The math and the safety layer, fully built and exhaustively tested, **before** any agent wiring. This is the project's spine — do it early and do it well.
📁 `geo/distance.py` (haversine, bearing), `geo/geofence.py` (point-in-polygon vs `fixtures/geo/imbl.geojson`), all five `guardrails/*.py` (`thresholds`, `freshness`, `resilience`, `provenance`, `templates`).
✅ The four mandatory guardrail test files (`docs/05 §7`) + `tests/test_geo_*.py` (known distance/bearing pairs; a point clearly inside and outside the IMBL buffer) all pass. Coverage on `guardrails/` and `geo/` should be effectively total — these run offline and must be bulletproof.

## M3 — Tools & fixtures (mock-first)
🎯 Every data/channel source reachable through the uniform adapter, reading deterministic fixtures.
📁 `tools/base.py` (interface + registry), `tools/incois.py`, `tools/imd.py`, `tools/isro.py`, `tools/channels/whatsapp.py`, `tools/channels/ivr.py` (each with Mock + Real-stub); `tools/copernicus.py` (scaffold); `scripts/seed_fixtures.py`; the fixtures from `docs/03 §7` / `docs/04 §5` (calm + cyclone cells).
✅ `tests/test_tools_*.py`: each mock returns a valid `ToolResponse(status=OK)` with `Measurement`s for a known cell; returns `EMPTY` for an unknown cell; a "force error" path returns `ERROR`. `fetch()` (resilience) records `data_freshness` on success. Real adapters raise `NotImplementedError` and carry a `# TODO(orca):` note.

## M4 — Agents + graph: first end-to-end (mock) answer
🎯 A query flows START→…→END and produces a sourced answer for **`pfz_nearest`**.
📁 `agents/channel_gateway.py`, `agents/router.py`, `agents/marine_data.py`, `agents/geospatial.py`, `agents/weather_risk.py`, `agents/synthesis.py`; `graph.py` (wire nodes + conditional fan-out + guardrail gate per `docs/01 §3`). Ocean-analytics/alert nodes exist as scaffold, not on the MVP path.
✅ `tests/test_end_to_end.py::test_pfz_nearest`: given a text query + location over the **calm** cell, the graph returns `final_response_text` naming the nearest zone with distance/bearing and a citation with a timestamp; every number passes the provenance check.

## M5 — Safety path + the failure behavior
🎯 The two remaining demo moments work: a tripped threshold and a killed source.
📁 Harden `weather_risk.py` (calls `thresholds.evaluate`, appends flags), the guardrail node wiring in `graph.py`, `synthesis.py` template/verdict handling.
✅ `test_end_to_end.py::test_safety_unsafe`: **cyclone** cell → a `DANGER` flag → answer is an unmistakable no-go built from the retrieved numbers, and the LLM narration cannot flip it. `::test_source_down`: force the weather tool to `ERROR` → `guardrail_status="failed"` → the `data_unavailable` template is spoken (with last-known + time if available), **no invented numbers**.

## M6 — Channels & web client
🎯 A human can actually talk to it.
📁 `api/ws.py` (WebSocket push-to-talk), `api/whatsapp.py` (webhook verify + inbound→graph→`whatsapp_send`), `api/ivr.py` (Exotel/Twilio media/TwiML → graph → `ivr_speak`), `clients/web/` (mic capture via Web Audio API → WS → play returned audio; text box fallback), `scripts/run_demo.py` (scripted 3-query run).
✅ Manual: open the web client, push-to-talk (mock ASR) "nearest fishing zone" → hear/see a sourced answer. `python scripts/run_demo.py` prints all three demo interactions end-to-end. WhatsApp/IVR routes accept a simulated inbound payload in tests and produce the right outbound call (asserted against the mock channel adapter).

## M7 — MCP exposure *(optional / scaffold)*
🎯 Expose the tools as an MCP server so external agents can reuse them.
📁 `src/orca/mcp/` — wrap the registry tools as MCP endpoints. Body may stay `# TODO(orca):` if time is short; the tools already work as typed Python.
✅ If built: an MCP client can list tools and call `incois_get_pfz` against fixtures. If skipped: documented as optional in README; nothing else depends on it.

## M8 — Hardening & demo polish
🎯 Make the demo reliable and the story legible.
📁 Fill `README.md` (architecture summary, the 3 demo moments, roadmap of 🟡/🔴 items), tighten logging/trace output so each run's agent path is visible, round out edge-case tests (missing location, `EMPTY` PFZ, stale-but-present reading → caution).
✅ Full `pytest -q` green; `ruff`/`black` clean; `run_demo.py` runs three times with identical, deterministic output; README lets a stranger set up and run the demo in <10 minutes.

---

## Definition of Done (MVP)
- `pfz_nearest` and `safety_check` both work end-to-end over mocks, across at least the web client (+ WhatsApp/IVR routes exercised in tests).
- The guardrail layer is fully implemented and exhaustively unit-tested; the three demo moments (`docs/07`) are reproducible.
- No live API calls anywhere; every real integration point is a `# TODO(orca):` stub with an honest note (`docs/04 §6`).
- All AI access is provider-agnostic (`llm/base.py`, `speech/base.py`); no agent imports a vendor SDK.
- Scaffolded pieces (Ocean Analytics, Alert & Notification, real adapters, MCP) exist as marked stubs — present, not completed, not deleted.
- `pytest -q` green and `ruff`/`black` clean from a fresh clone with **no** keys and **no** network.

## What NOT to do (recurring failure modes to avoid)
- Don't let the LLM compute distances, pick the verdict, or emit a number that isn't a `Measurement`.
- Don't put retry/threshold logic inside a tool adapter — that belongs in `guardrails/`.
- Don't skip ahead to channels (M6) before the guardrail (M2) and end-to-end (M4/M5) are green.
- Don't "temporarily" hard-code an API key or a threshold outside its module.
- Don't fully build the scaffolded agents because they seem interesting — scope discipline is graded (by the clock, if nothing else).
