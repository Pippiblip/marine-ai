# 01 — Architecture

This document is the mental model. `docs/03-data-contracts.md` gives the exact types; `docs/06-build-plan.md` gives the build order. Read this to understand *how the pieces fit and why*.

## 1. The one-brain, many-channels shape

Three channels (web push-to-talk, WhatsApp, phone/IVR) all funnel into **one** reasoning pipeline. The channel only handles transport and speech I/O; all intelligence lives in the shared graph. A fisherman on a feature phone dialing a number gets exactly the same brain as an app user.

```
   ┌──────────────── ACCESS CHANNELS ────────────────┐
   │  Web push-to-talk │ WhatsApp Cloud API │ Phone/IVR│
   └───────────────────────┬──────────────────────────┘
                            │ audio / text  + user geo
                            ▼
   ┌──────────────────────────────────────────────────┐
   │ CHANNEL GATEWAY AGENT                              │
   │ normalize input → one schema; ASR (speech→text),  │
   │ language ID, translate→EN; queue TTS on the reply │
   └───────────────────────┬──────────────────────────┘
                            │ {query_text_en, source_lang, user_location, channel}
                            ▼
   ┌──────────────────────────────────────────────────┐
   │ ROUTER & PLANNING AGENT                            │
   │ classify intent → build subtask list;             │
   │ owns the shared LangGraph state                   │
   └──┬──────────────┬───────────────┬─────────────────┘
      ▼              ▼               ▼
 ┌──────────┐ ┌────────────┐ ┌─────────────┐ ┌──────────────┐
 │ MARINE   │ │ WEATHER &  │ │ GEOSPATIAL  │ │ OCEAN        │
 │ DATA     │ │ RISK       │ │ REASONING   │ │ ANALYTICS    │ (scaffold/v2)
 │ DISCOVERY│ │ (only one  │ │ Haversine,  │ │ historical   │
 │ PFZ/SST/ │ │ that can   │ │ point-in-   │ │ trends       │
 │ chloro   │ │ raise a    │ │ polygon,    │ │ (Copernicus) │
 │          │ │ SafetyFlag)│ │ IMBL/MPA    │ │              │
 └────┬─────┘ └─────┬──────┘ └──────┬──────┘ └──────┬───────┘
      │             │               │               │
      │  each calls TOOLS ──────────┴───────────────┘
      │  (incois · imd · isro · copernicus adapters — MOCK-FIRST)
      └──────────────────────┬───────────────────────
                             ▼
   ┌──────────────────────────────────────────────────┐
   │ GUARDRAIL & CONFIDENCE LAYER  (deterministic code) │
   │ hard thresholds · staleness/timestamp checks ·     │
   │ source binding · number-provenance check ·         │
   │ explicit-failure templates                         │
   └───────────────────────┬──────────────────────────┘
                            ▼
   ┌──────────────────────────────────────────────────┐
   │ SYNTHESIS & VOICE AGENT                            │
   │ compose ONE evidence-cited answer (only after      │
   │ checking safety_flags + data_freshness); TTS       │
   └───────────────────────┬──────────────────────────┘
                            ▼
                back to the originating channel

   ┌──────────────────────────────────────────────────┐
   │ ALERT & NOTIFICATION AGENT (always-on, scaffold)   │
   │ watches cyclone/swell polygons → push to users     │
   └──────────────────────────────────────────────────┘
```

## 2. Why multiple agents (have this answer ready — judges will ask)

A single prompt could *look* like it does this. The multi-agent split earns its keep for three concrete reasons, and the architecture must preserve all three:

1. **Separation for safety.** Only the Weather & Risk agent may append a `SafetyFlag`, and it does so via hard-coded thresholds — not the LLM. Isolating that authority in one place is what makes the safety path auditable.
2. **Source attribution.** Each specialist owns exactly one data domain, so every fact in the final answer is traceable to the agent (and tool, and timestamp) that produced it. No "where did this number come from?"
3. **Parallelism.** Fishing-zone, weather, and geospatial lookups are independent and run concurrently, which is how you hit a snappy response despite several data calls.

## 3. Orchestration: LangGraph + one shared state

Use **LangGraph** as a stateful graph, not a linear script. Each agent is a **node**; the graph holds **one shared state object** (`PlatformState`, see `docs/03-data-contracts.md`) that every node reads from and writes its own slice into. No node overwrites another node's slice.

Why LangGraph specifically (not a plain function chain):
- **Shared, checkpointed state** across the whole run — you can pause, resume, and inspect every step, which is essential when debugging a safety system.
- **Conditional edges + loops**, not just a straight pipeline — the router decides which specialists run; the guardrail can force a retry loop before synthesis.
- **Traceability** — you can log the exact state at each node transition (wire this to LangSmith or plain structured logs).

### Node graph (MVP)

```
START
  → channel_gateway            (ASR, language id, translate→EN, resolve location)
  → router                     (set intent + subtasks)
  → [conditional fan-out by subtasks]
        marine_data            (if "marine_data" in subtasks)
        weather_risk           (if "weather_risk" in subtasks)
        geospatial             (if "geospatial" in subtasks)
  → guardrail                  (deterministic checks over all results; may set failure state)
  → synthesis                  (compose answer; TTS)
  → END
```

- `channel_gateway` and `router` always run.
- The three specialists are **conditional** on the router's `subtasks` list and run **in parallel** where the framework allows (fan-out → join before `guardrail`).
- `guardrail` always runs and is the gate before `synthesis`. If the guardrail marks the run as failed/stale, `synthesis` must emit the explicit-failure template rather than a normal answer.
- `ocean_analytics` is a node that exists but is only added to the graph path when intent requires it (scaffold — not reached by the two MVP intents).
- The `alert` agent is **not** in this request/response graph — it's a separate always-on background loop (scaffold).

### Intent → subtasks mapping (MVP)

| Intent | Agents invoked | Notes |
|--------|----------------|-------|
| `pfz_nearest` | marine_data → geospatial (→ weather_risk for a safety check on the chosen zone) | Weather is included so the answer can say "and it's clear/unsafe there." |
| `safety_check` | weather_risk → geospatial (for the user's cell/area) | The safety-critical path; guardrail thresholds central. |
| `boundary_check` *(scaffold)* | geospatial | IMBL proximity; wire minimally if time. |
| `conditions_summary` *(scaffold)* | weather_risk | Stub. |

## 4. Request lifecycle (trace one query)

For *"Is it safe to go out tomorrow morning?"* (Tamil, over the web client):

1. **Channel Gateway** receives audio over a WebSocket, runs ASR (mock or Bhashini) → text, detects `source_lang=ta-IN`, translates to English, resolves `user_location` (from the client's GPS or a saved profile).
2. **Router** classifies `intent=safety_check`, sets `subtasks=["weather_risk","geospatial"]`.
3. **Weather & Risk** calls `imd_get_marine_warnings` + `incois_get_ocean_state` (mock adapters) for the user's cell → returns `{wave_height_m, wind_speed_kt, cyclone_distance_km, …}` each with a `retrieved_at` timestamp; then applies the hard-coded threshold and, if breached, appends a `SafetyFlag`.
4. **Geospatial** confirms the cell and checks IMBL proximity.
5. **Guardrail** verifies freshness (is the wave reading recent enough?), that all numbers came from tool responses, retries/serves-cached/marks-failed as needed, and finalizes `safety_flags`.
6. **Synthesis** — because a safety flag is present — composes a red-alert answer from the *retrieved* numbers, appends source + timestamp, and TTS renders it in Tamil, streamed back into the channel.

## 5. Layering (keep these boundaries clean)

```
channels/api  ──uses──▶  graph (agents)  ──uses──▶  guardrails + tools + geo + llm + speech
```

- **Agents** contain orchestration/domain logic and may call the LLM (via the interface) and tools.
- **Guardrails, geo, tools** are **pure/deterministic** and must not call the LLM.
- **llm** and **speech** are thin provider-agnostic interfaces.
- **api/channels** know nothing about domain logic — they marshal transport in/out of the graph.

Keep `src/orca/graph.py` a thin composition file. All real logic lives in the node modules and the deterministic modules. This separation is what lets the guardrail and geo code be unit-tested offline, which is both good engineering and the core of the demo.
