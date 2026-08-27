# 02 — Tech stack & setup

## 1. Stack (use these; don't add others without a `# TODO(orca):` note)

| Layer | Choice | Version (min) | Notes |
|-------|--------|---------------|-------|
| Language | Python | 3.11 | Type hints everywhere. |
| Package/dep mgmt | `uv` (preferred) or `pip` + `pyproject.toml` | latest | `uv` is faster; either is fine. |
| Web framework | FastAPI | 0.110+ | async, WebSocket support for push-to-talk. |
| ASGI server | Uvicorn | 0.29+ | `uvicorn orca.api.app:app --reload`. |
| Orchestration | LangGraph | 0.2+ | stateful multi-agent graph. |
| LLM SDK (default) | `anthropic` | 0.39+ | behind the `LLMClient` interface; **never imported by agents directly**. |
| LLM SDK (optional) | `openai` | 1.40+ | optional alt impl of `LLMClient`. |
| Data models | Pydantic | v2 (2.6+) | all cross-boundary types; `pydantic-settings` for config. |
| Geospatial | `shapely` | 2.0+ | point-in-polygon geofencing. |
| Geospatial | `geopandas` | 0.14+ | shapefile loading (IMBL/MPA); optional if you keep polygons as GeoJSON. |
| Distance | `haversine` (or hand-rolled) | latest | nearest-zone bearing/distance. Hand-rolled is fine and testable. |
| HTTP client | `httpx` | 0.27+ | for real adapters later; not used by mocks. |
| Cache/state | `redis` + a `fakeredis` fallback | 5.0+ | freshness map, circuit-breaker state, advisory cache. Use fakeredis in tests/dev. |
| DB (optional MVP) | PostgreSQL + PostGIS via SQLAlchemy 2.0 | — | users, saved locations, geofences. **In-memory/SQLite acceptable for MVP**; PostGIS is a `# TODO(orca):` upgrade. |
| Data science | `xarray` + `netCDF4` | latest | **scaffold only** — Copernicus/NetCDF path is v2. |
| Testing | pytest + pytest-asyncio | latest | offline, fixtures only. |
| Lint/format | ruff + black | latest | `ruff check` + `black .`. |
| Web client | Vanilla HTML/JS + Web Audio API (or minimal Vite) | — | browser push-to-talk; keep it dependency-light. |

**Speech (ASR/TTS):** no hard dependency in the MVP. The default `MockSpeech` implementation returns canned transcripts/audio so the pipeline runs with zero keys. A `BhashiniSpeech` adapter is stubbed (`httpx`-based) behind the same interface. Self-hosted AI4Bharat models (IndicTrans2 / IndicConformer / Indic-TTS) are a documented `# TODO(orca):` alternative.

## 2. Repository layout (create exactly this)

```
orca/
├─ AGENTS.md                      # provided — the operating manual
├─ README.md                      # YOU generate (setup/run/test/demo)
├─ pyproject.toml                 # YOU generate
├─ .env.example                   # YOU generate (see §4)
├─ .cursor/rules/orca.mdc         # provided
├─ docs/                          # provided — the spec (read-only for you)
├─ agents/                        # provided — per-agent contracts (read-only for you)
├─ src/orca/
│  ├─ __init__.py
│  ├─ config.py                   # Pydantic Settings; env → typed config
│  ├─ schemas.py                  # ALL shared Pydantic models (see docs/03)
│  ├─ state.py                    # PlatformState (LangGraph state), SafetyFlag
│  ├─ graph.py                    # thin: builds the LangGraph, wires nodes/edges
│  ├─ logging.py                  # structured logging + per-run trace id
│  ├─ llm/
│  │  ├─ base.py                  # LLMClient protocol/ABC
│  │  ├─ mock.py                  # DEFAULT (ORCA_LLM_PROVIDER=mock) — keyword classify + template narrate, offline
│  │  ├─ claude.py                # default REAL provider (needs ANTHROPIC_API_KEY)
│  │  ├─ openai.py                # optional impl
│  │  └─ factory.py               # get_llm(): picks impl from config
│  ├─ speech/
│  │  ├─ base.py                  # SpeechClient protocol (asr, tts, detect_lang)
│  │  ├─ mock.py                  # DEFAULT — canned, offline
│  │  └─ bhashini.py              # stub adapter  # TODO(orca)
│  ├─ agents/
│  │  ├─ channel_gateway.py
│  │  ├─ router.py
│  │  ├─ marine_data.py
│  │  ├─ weather_risk.py
│  │  ├─ geospatial.py
│  │  ├─ synthesis.py
│  │  ├─ ocean_analytics.py       # scaffold  # TODO(orca)
│  │  └─ alert.py                 # scaffold  # TODO(orca)
│  ├─ guardrails/
│  │  ├─ thresholds.py            # SAFETY: hard-coded rules
│  │  ├─ freshness.py             # staleness / timestamp logic
│  │  ├─ resilience.py            # retry+backoff, circuit breaker
│  │  ├─ provenance.py            # "every number in output exists in retrieved data"
│  │  └─ templates.py             # explicit-failure + disclaimer templates
│  ├─ tools/
│  │  ├─ base.py                  # Tool interface + registry; MockAdapter/RealAdapter split
│  │  ├─ incois.py                # incois_get_pfz, incois_get_ocean_state
│  │  ├─ imd.py                   # imd_get_marine_warnings (CAP-XML shape)
│  │  ├─ isro.py                  # isro_get_chlorophyll (satellite EO)
│  │  ├─ copernicus.py            # scaffold  # TODO(orca)
│  │  └─ channels/
│  │     ├─ whatsapp.py           # whatsapp_send
│  │     └─ ivr.py                # ivr_speak
│  ├─ geo/
│  │  ├─ distance.py              # haversine, bearing
│  │  └─ geofence.py              # point-in-polygon vs IMBL/MPA
│  ├─ api/
│  │  ├─ app.py                   # FastAPI app, /health, includes routers
│  │  ├─ ws.py                    # WebSocket for web push-to-talk
│  │  ├─ whatsapp.py              # webhook route
│  │  └─ ivr.py                   # telephony media route
│  ├─ fixtures/                   # mock data (see docs/03 §Fixtures)
│  │  ├─ pfz/…                    # GeoJSON PFZ nodes per bounding box
│  │  ├─ weather/…                # marine warnings, ocean state
│  │  ├─ geo/imbl.geojson         # boundary polygon(s)
│  │  └─ speech/…                 # canned transcripts/audio for MockSpeech
│  └─ mcp/                        # M7 (optional): MCP server exposure  # TODO(orca)
├─ clients/
│  └─ web/                        # browser push-to-talk client (HTML/JS)
├─ tests/
│  ├─ test_guardrails_*.py        # MANDATORY
│  ├─ test_geo_*.py
│  ├─ test_tools_*.py
│  ├─ test_agents_*.py
│  └─ test_end_to_end.py          # both intents over fixtures + the kill-source path
└─ scripts/
   ├─ seed_fixtures.py            # generate/refresh fixture data
   └─ run_demo.py                 # scripted 3-query demo (see docs/07)
```

## 3. Provider-agnostic interfaces (build these in M0/M1, before any agent)

### `src/orca/llm/base.py`

```python
from typing import Protocol, Sequence
from pydantic import BaseModel

class LLMMessage(BaseModel):
    role: str            # "system" | "user" | "assistant"
    content: str

class LLMClient(Protocol):
    def classify(self, text: str, labels: Sequence[str], *, system: str | None = None) -> str:
        """Return exactly one label from `labels`. Used by the Router. Deterministic prompt."""
        ...
    def narrate(self, facts: dict, *, system: str, max_words: int = 60) -> str:
        """Turn already-retrieved facts into ONE plain sentence. MUST NOT add numbers not in `facts`."""
        ...
    def complete(self, messages: Sequence[LLMMessage], *, temperature: float = 0.0) -> str:
        ...
```

- `claude.py` implements this with the `anthropic` SDK; `openai.py` optionally with `openai`.
- `factory.py` reads `ORCA_LLM_PROVIDER` (`claude` | `openai` | `mock`) and returns the impl. Provide a `MockLLM` too so tests and the offline demo need no API key (it can do keyword-based intent classification and template narration).
- **Agents import `get_llm()` from the factory. They never import `anthropic`/`openai`.**

### `src/orca/speech/base.py`

```python
class SpeechClient(Protocol):
    def detect_language(self, audio: bytes) -> str: ...
    def asr(self, audio: bytes, lang: str) -> str: ...          # speech → text
    def translate(self, text: str, src: str, tgt: str) -> str:  # regional ↔ English
        ...
    def tts(self, text: str, lang: str) -> bytes: ...           # text → speech
```

- `mock.py` is the **default** (`ORCA_SPEECH_PROVIDER=mock`): returns fixture transcripts, echoes translation, returns a short silent/canned WAV for TTS. Lets the whole pipeline run offline.
- `bhashini.py` is a stub calling the Bhashini pipeline API via `httpx` — body `# TODO(orca): wire Bhashini ULCA pipeline`.

## 4. Configuration & env vars

`src/orca/config.py` uses `pydantic-settings`. Provide `.env.example`:

```dotenv
# --- AI providers (all optional in MVP; defaults run fully offline) ---
ORCA_LLM_PROVIDER=mock            # mock | claude | openai
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
ORCA_SPEECH_PROVIDER=mock         # mock | bhashini
BHASHINI_API_KEY=
BHASHINI_USER_ID=

# --- Data mode ---
ORCA_DATA_MODE=mock               # mock | real   (real is scaffold/TODO)

# --- Infra (optional in MVP) ---
ORCA_REDIS_URL=                   # empty → use fakeredis
ORCA_DATABASE_URL=                # empty → in-memory/SQLite

# --- Channels (only needed to run those channels live) ---
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
EXOTEL_SID=
EXOTEL_TOKEN=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# --- Guardrail tuning (defaults live in code; env overrides for demo) ---
ORCA_WAVE_UNSAFE_M=2.5
ORCA_WIND_UNSAFE_KT=25
ORCA_FRESHNESS_MAX_MIN_SAFETY=30
ORCA_FRESHNESS_MAX_HOURS_PFZ=6
```

**Important:** the guardrail thresholds have safe defaults *in code* (`guardrails/thresholds.py`); env vars only override them for demo staging. Never require an env var to be set for a safety default to exist.

## 5. Setup & run commands (document these in the README you generate)

```bash
# install
uv sync                # or: pip install -e ".[dev]"

# run tests (must pass fully offline, no keys)
pytest -q

# lint/format
ruff check . && black --check .

# run the API (defaults: mock LLM, mock speech, mock data)
uvicorn orca.api.app:app --reload
# → GET http://localhost:8000/health  ⇒ {"status":"ok"}

# open the web client
#   serve clients/web/ (e.g. `python -m http.server` in that dir) and point it at ws://localhost:8000/ws

# run the scripted demo
python scripts/run_demo.py
```

The whole system must **boot and demo with no API keys and no network**, thanks to the mock LLM, mock speech, and fixture data. Real providers are opt-in via the env vars above.
