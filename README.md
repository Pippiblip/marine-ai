# ORCA — Marine EcOsystem Reasoning with Collaborative Agents

A voice-first, multi-agent system that turns India's ocean and satellite data into spoken, evidence-backed answers for coastal fishermen, over channels they can afford: web push-to-talk, WhatsApp, and phone/IVR.

**This is a Smart India Hackathon 2026 project for ISRO problem statement 26176 (Disaster Management).**


---

## Quick Start

### Prerequisites
- Python 3.9+
- `pip` or `uv` (package manager)

### Installation

Clone the repository and install the package:

```bash
cd marine-ai
pip install -e ".[dev]"
```

This installs ORCA and all development dependencies. **No API keys are required** — the system runs fully offline with mock LLM, mock speech, and fixture data.

### Run the API

```bash
uvicorn orca.api.app:app --reload
```

The API will start on `http://localhost:8000`. Check health:

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.0.1"}
```

### Run Tests

```bash
pytest -q
```

All tests run **offline, deterministically, with no API keys**. The mock LLM, mock speech, and fixture data make this possible.

### Code Quality

```bash
ruff check .
black --check .
```

---

## Architecture Overview

ORCA is a multi-agent orchestration system built on **LangGraph**. Here's how it works:

```
Web / WhatsApp / Phone
         ↓
   Channel Gateway (ASR, language detection, translation)
         ↓
   Router (intent classification, task breakdown)
         ↓
   Parallel Agents:
      - Marine Data (fishing zones, chlorophyll, SST)
      - Weather & Risk (waves, wind, cyclone proximity)
      - Geospatial (Haversine distance, IMBL boundary check)
         ↓
   Guardrail Layer (deterministic safety logic, freshness checks, retries)
         ↓
   Synthesis (compose answer, check provenance, TTS)
         ↓
   Back to user (web / WhatsApp / phone)
```

**The key differentiator:** The guardrail layer is 100% deterministic Python. Safety verdicts come from hard-coded thresholds, never from the LLM. Every number is bound to its source and retrieval time. If data is stale or missing, the system says so explicitly — it never invents an answer.

---

## Configuration

All settings are loaded from environment variables. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Important:** The system runs fully offline with default settings:
- `ORCA_LLM_PROVIDER=mock` — uses a mock LLM (keyword classification + template narration)
- `ORCA_SPEECH_PROVIDER=mock` — uses mock speech (fixture transcripts + canned audio)
- `ORCA_DATA_MODE=mock` — reads fixture data, not live APIs

Override these only if you have API keys and want to use real providers (not recommended for local development or testing).

### Safety Thresholds (code defaults, env override for demo)

```env
ORCA_WAVE_UNSAFE_M=2.5           # waves above 2.5 m → unsafe
ORCA_WIND_UNSAFE_KT=25           # wind above 25 kt → unsafe
ORCA_CYCLONE_NEAR_KM=300         # cyclone within 300 km → unsafe
ORCA_SWELL_UNSAFE_M=2.0          # swell above 2.0 m → warning
```

### Freshness Windows

```env
ORCA_FRESHNESS_MAX_MIN_SAFETY=30  # safety readings must be < 30 min old
ORCA_FRESHNESS_MAX_HOURS_PFZ=6    # PFZ advisories can be up to 6 hours old
```

---

## Project Status

**Current Milestone: M0 — Skeleton & config** ✅

| Milestone | Status | Summary |
|-----------|--------|---------|
| M0 | ✅ Done | Skeleton, config, `/health` endpoint |
| M1 | ⏳ TODO | Contracts, interfaces, mock LLM/speech |
| M2 | ⏳ TODO | Deterministic core (geo, guardrails) |
| M3 | ⏳ TODO | Tools, fixtures (mock adapters) |
| M4 | ⏳ TODO | Agents, graph (end-to-end `pfz_nearest`) |
| M5 | ⏳ TODO | Safety path, failure behavior |
| M6 | ⏳ TODO | Channels, web client |
| M7 | ⏳ TODO | MCP exposure (optional) |
| M8 | ⏳ TODO | Hardening, demo polish |

---

## Golden Rules

This is safety-critical software. To ensure trustworthiness, we enforce seven rules:

1. **The LLM never invents a number.** Every wave height, wind speed, or coordinate must come from a tool response or deterministic code.
2. **Safety verdicts are hard-coded, not the LLM.** Thresholds are immutable Python; the model narrates, it doesn't decide.
3. **Every number carries provenance.** Timestamp, source, observation time — all baked in.
4. **Mock-first.** All tools read fixtures by default; real adapters are stubs.
5. **Provider-agnostic AI.** LLM and speech go through interfaces, not vendor SDKs.
6. **Scope discipline.** MVP fully built, everything else scaffolded with `# TODO(orca):`.
7. **Determinism in code, language in the LLM.** Math and safety logic are pure, tested Python; only narration and translation touch the model.

---

## Roadmap (v2 & beyond)

🟡 **Scaffolded for future work** (stubs in place, not fully built):
- Ocean Analytics Agent (historical trends via Copernicus)
- Alert & Notification Agent (proactive cyclone/swell warnings)
- Real data adapters (INCOIS, IMD, ISRO, Copernicus, Bhashini)
- MCP server exposure (M7)

🔴 **Out of scope** (noted for reference, not built):
- Native Android/iOS apps (web client is the stand-in)
- On-device offline inference
- Deep-sea connectivity beyond cellular

---

## License

MIT License. See `LICENSE` file for details.

---

## Contributing

This is an active hackathon project. Contributions welcome; follow the structure in `AGENTS.md` and `docs/`.

---

## Questions?

See the specification:
- `AGENTS.md` — operating manual and golden rules
- `docs/00-overview.md` — the vision and scope
- `docs/01-architecture.md` — system design and data flow
- `docs/02-tech-stack-and-setup.md` — stack and repository layout
- `docs/03-data-contracts.md` — all shared Pydantic models
- `docs/04-mcp-tools.md` — tool contracts and adapters
- `docs/05-guardrails.md` — the safety layer (the heart)
- `docs/06-build-plan.md` — milestones and acceptance tests
- `docs/07-testing-and-demo.md` — how to test and the three demo moments