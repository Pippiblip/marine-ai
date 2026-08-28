# ORCA — Marine EcOsystem Reasoning with Collaborative Agents

A voice-first, multi-agent system that turns India's ocean and satellite data into spoken, evidence-backed answers for coastal fishermen, over channels they can afford: web push-to-talk, WhatsApp, and phone/IVR.

**This is a Smart India Hackathon 2026 project for ISRO problem statement 26176 (Disaster Management).**

---

## Quick start (offline, no keys)

```bash
cd marine-ai
pip install -e ".[dev]"     # or: uv sync

pytest -q                   # must pass with no network

uvicorn orca.api.app:app --reload
# → http://localhost:8000          push-to-talk web client
# → GET /health                    {"status":"ok","version":"0.0.1"}

python scripts/run_demo.py  # three demo moments, identical on repeat
python scripts/seed_fixtures.py
```

Open **http://localhost:8000**. The yellow banner is intentional: this run is **fixture mode**. Click **1 · Fishing zone**, then **2 · Safety no-go**, then **3 · Kill weather**. Browser speech reads the guardrail-approved sentence (not a live TTS vendor).

**WhatsApp on your phone (real app):** see **http://localhost:8000/whatsapp/connect**. You need a Meta Cloud API test number, `ORCA_WHATSAPP_MODE=live`, and HTTPS (ngrok) so Meta can POST to `/webhooks/whatsapp`. Then you message that business number from your WhatsApp. Replies are text plus a voice note when macOS `say` is available. Typed questions work the same as the web demo (`cyclone` / `kill weather` pick the fixture). Inbound voice notes need Bhashini; otherwise type.

**WhatsApp (browser mock, no Meta account):** http://localhost:8000/whatsapp

### What to say to judges

- *These numbers are realistic INCOIS/IMD/ISRO products in the same shape as production. Live portals are not a public JSON API; adapters are the swap point.*
- *I can rephrase the model. I cannot make moment 2 say “safe” — the 2.5 m rule is unit-tested Python.*
- *Moment 3 is the thesis: wrong-and-confident can kill someone. We refuse to guess.*
- *Why several agents: only Weather & Risk may raise a SafetyFlag; every fact traces to one specialist.*

---

## The three demo moments

1. **Capability** — “Where is the nearest fishing zone?” on the **calm** cell. Sourced, timestamped distance/bearing from INCOIS PFZ (plus ISRO chlorophyll).
2. **Deterministic safety** — “Is it safe to go out?” on the **cyclone** cell. A hard-coded threshold (`wave > 2.5 m`) forces **Do not go out**. The LLM cannot flip the verdict.
3. **Trust** — kill the weather source and re-ask. The reply is the explicit-failure template plus last-known reading and time — **no invented numbers**.

---

## Architecture

Three channels funnel into one LangGraph:

`channel_gateway → router → specialists (marine / weather / geo) → guardrail → synthesis`

- Only **Weather & Risk** may append a `SafetyFlag`, and only via `guardrails/thresholds.py`.
- Every number that reaches the user is a `Measurement` (value, unit, source, timestamp). Synthesis runs `provenance.verify` before speaking.
- Tools are mock adapters over `src/orca/fixtures/`. Real adapters exist as `# TODO(orca):` stubs.

---

## Configuration

Copy `.env.example` to `.env`. Defaults run fully offline:

- `ORCA_LLM_PROVIDER=mock`
- `ORCA_SPEECH_PROVIDER=mock`
- `ORCA_DATA_MODE=mock`

Safety thresholds live in code (`guardrails/thresholds.py`); env vars only override them for demo staging.

---

## Project status

MVP **M0–M6 + M8** is implemented. M7 (MCP) is scaffolded.

| Milestone | Status |
|-----------|--------|
| M0 Skeleton & config | done |
| M1 Contracts & interfaces | done |
| M2 Geo + guardrails | done |
| M3 Tools & fixtures | done |
| M4 Agents + graph (`pfz_nearest`) | done |
| M5 Safety path + source kill | done |
| M6 Web / WhatsApp / IVR | done |
| M7 MCP exposure | scaffold (`src/orca/mcp/`) |
| M8 Demo polish | done |

---

## Roadmap

🟡 Scaffolded (present, not fully built): Ocean Analytics, Alert & Notification, real INCOIS/IMD/ISRO/Copernicus/Bhashini adapters, MCP server.

🔴 Out of scope: native mobile apps, on-device inference, deep-sea connectivity beyond cellular.

---

## License

MIT. See the specification in `AGENTS.md` and `docs/`.
