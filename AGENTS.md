# AGENTS.md — Operating manual for the coding agent building ORCA

> **Read this file first, in full, before writing any code.** It tells you what you are building, the rules you must never break, the order to build in, and how to know when you are done. Every other spec file is referenced from here.

You are building **ORCA — Marine EcOsystem Reasoning with Collaborative Agents**: a voice-first, multi-agent system that turns India's ocean and satellite data into spoken, evidence-backed answers for coastal fishermen, over a web app, WhatsApp, and a phone call. This is a Smart India Hackathon 2026 project responding to ISRO problem statement 26176 (Theme: Disaster Management).

You are building this **from scratch** in an empty repository. The `docs/` and `agents/` folders in this repo are your specification. You generate everything else (`src/`, `clients/`, `tests/`, config, etc.).

---

## 1. How to read the specification

Read these in order once, then keep them open as you build:

| # | File | What it gives you |
|---|------|-------------------|
| 1 | `docs/00-overview.md` | The vision, the users, and — critically — **what is in scope now (MVP) vs. scaffolded for later**. |
| 2 | `docs/01-architecture.md` | The components, how data flows, and the LangGraph orchestration + shared state. |
| 3 | `docs/02-tech-stack-and-setup.md` | Pinned stack, the exact **repo layout you must create**, env vars, and run commands. |
| 4 | `docs/03-data-contracts.md` | The `PlatformState`, `SafetyFlag`, tool request/response schemas, and the mock-fixture format. |
| 5 | `docs/04-mcp-tools.md` | The contract for every data/channel tool (`incois_get_pfz`, `imd_get_marine_warnings`, …). |
| 6 | `docs/05-guardrails.md` | The deterministic guardrail layer — **the heart of this project**. Read it twice. |
| 7 | `docs/06-build-plan.md` | The phased milestones **M0–M8**. This is your build order. Follow it. |
| 8 | `docs/07-testing-and-demo.md` | How to test each milestone and the live demo the code must support. |
| — | `agents/01…08-*.md` | The contract for each individual agent. Open the one you're implementing. |

When a spec file and this file disagree, **this file wins**. When you are unsure, prefer the **simplest thing that satisfies the acceptance test in `docs/06-build-plan.md`** and leave a `# TODO(orca):` comment explaining the assumption.

---

## 2. The golden rules (never break these)

These are non-negotiable. They come from the fact that ORCA gives **go/no-go safety advice to people whose lives depend on it.** A wrong wave-height answer during a cyclone can kill someone.

1. **The LLM never invents a number.** Every wave height, wind speed, coordinate, distance, depth, or timestamp that reaches the user must come from a tool response or a deterministic calculation in code. The LLM's only jobs are: (a) classify intent, and (b) narrate already-retrieved facts into a sentence. See `docs/05-guardrails.md`.

2. **Safety verdicts are deterministic Python, not the LLM.** "Is 2.8 m safe?" is answered by a hard-coded function (`wave_height_m > 2.5 or wind_speed_kt > 25 → unsafe`), never by the model. The model may phrase the verdict; it may not decide it or soften it.

3. **Every number carries a timestamp and a source.** If data is stale or missing, the system says so out loud with an explicit template — it does **not** guess or stay silent. "Explicit failure over confident silence."

4. **Mock-first.** Do **not** wire live INCOIS / IMD / ISRO / Copernicus / Bhashini endpoints in the MVP. Build every tool as an adapter that reads realistic **fixtures** (`src/orca/fixtures/`) behind a uniform interface, and leave a clearly-marked `RealAdapter` stub with a `# TODO(orca): wire live endpoint` for later. This keeps the build unblocked and the demo reliable. See `docs/04-mcp-tools.md`.

5. **Provider-agnostic AI.** All LLM calls go through one interface (`src/orca/llm/base.py`); the default implementation is Anthropic Claude, selected by env var. Never call a vendor SDK directly from an agent. Speech (ASR/TTS) goes through `src/orca/speech/base.py` with a mock implementation as the default so the pipeline runs with zero external keys.

6. **Scope discipline (MVP-first, full scaffold).** Fully implement only the MVP slice defined in `docs/00-overview.md` §Scope: two intents (`pfz_nearest`, `safety_check`), the guardrail layer, and the agents they need. **Scaffold** everything else (Ocean Analytics agent, Alert & Notification agent, real adapters, native mobile) — create the file, the class, the interface, and a `# TODO(orca):` body, but do not fully build it. Never delete a scaffold; never fully implement one unless the build plan says so.

7. **Determinism lives in code, language lives in the LLM.** Geospatial math (Haversine, point-in-polygon), threshold checks, retries, and freshness logic are plain Python and must be unit-tested. Only translation and narration touch the model.

If following a rule seems to block progress, **stop and leave a `# TODO(orca):` note rather than violating it.** These rules are the project's entire technical differentiation.

---

## 3. Build order

Follow `docs/06-build-plan.md` milestone by milestone. Do not jump ahead. Each milestone has a concrete **acceptance test** — do not start milestone *N+1* until milestone *N*'s test passes.

```
M0  Skeleton & config        → repo layout, config, pytest runs, GET /health OK
M1  Contracts & interfaces    → all schemas + PlatformState + mock LLM/speech behind interfaces
M2  Deterministic core        → geo math + the full guardrail layer, exhaustively TESTED (the spine)
M3  Tools & fixtures (mock)    → every tool returns fixture data + timestamps; resilience records freshness
M4  Agents + graph (e2e)      → pfz_nearest flows START→END and returns a sourced, timestamped answer
M5  Safety path + failure      → tripped-threshold no-go AND killed-source explicit-failure both work
M6  Channels + web client      → query round-trips over the web push-to-talk client end-to-end
M7  MCP exposure (optional)    → wrap tools as MCP server; document mock→real switch (may stay TODO)
M8  Hardening & demo polish    → the 3-query demo (incl. deliberate data-source kill) runs reliably
```

MVP "done" = **M0 through M6 complete and demoable**, with M8's demo script working. M7 and the scaffolded agents are stretch. The one-liners above are a map; `docs/06-build-plan.md` has each milestone's files and acceptance test — build against those.

---

## 4. Conventions

- **Language/stack:** Python 3.11+, FastAPI, LangGraph, Pydantic v2, pytest. Full list and versions in `docs/02-tech-stack-and-setup.md`. Do not introduce a dependency that isn't listed there without adding a `# TODO(orca):` note explaining why.
- **Typing:** every function signature is fully type-hinted. Tool inputs/outputs are Pydantic models from `src/orca/schemas.py`. No untyped `dict` crossing a module boundary.
- **Structure:** one agent per file under `src/orca/agents/`, one tool per file under `src/orca/tools/`. Keep the LangGraph wiring in `src/orca/graph.py` thin — it composes nodes, it doesn't contain logic.
- **Tests:** every deterministic module (guardrails, geo, tools) ships with unit tests in `tests/`. The guardrail tests are mandatory and are part of the demo story.
- **Config:** all secrets and switches via env vars loaded in `src/orca/config.py` (Pydantic Settings). Provide `.env.example`. Never hard-code a key or a threshold value outside its designated module.
- **Comments:** use `# TODO(orca): …` for every deferred/scaffolded piece so they're greppable. Use `# SAFETY:` to mark any code on the safety-critical path.
- **Commits:** one commit per milestone minimum, message prefixed with the milestone id (e.g. `M3: deterministic guardrail layer + tests`).
- **No network in tests.** Tests run fully offline against fixtures.

---

## 5. Definition of done (MVP)

You are done with the MVP when all of the following are true:

- [ ] `pip install -e .` (or `uv sync`) succeeds and `pytest` passes with **zero network access**.
- [ ] `uvicorn orca.api.app:app` starts; `GET /health` returns `{"status":"ok"}`.
- [ ] The two intents `pfz_nearest` and `safety_check` each produce a correct, **evidence-cited, timestamped** spoken answer over fixture data.
- [ ] The guardrail layer is real and tested: hard threshold verdicts, staleness handling, retry+backoff, circuit breaker, and the explicit-failure template.
- [ ] The **deliberate data-source kill** demo works: disable a tool and re-ask — the system replies with the explicit-failure template and the last known reading + time, and **never invents coordinates**.
- [ ] A query round-trips end-to-end over the **web push-to-talk client**; WhatsApp and IVR handlers exist and are wired (test stubs acceptable for the MVP).
- [ ] Ocean Analytics and Alert & Notification agents exist as **scaffolds** with `# TODO(orca):` bodies, not deleted, not fully built.
- [ ] `README.md` (which you generate) documents setup, run, test, and the demo script from `docs/07-testing-and-demo.md`.

When in doubt, re-read §2. The guardrail behavior is the thing that must work perfectly; everything else is supporting cast.
