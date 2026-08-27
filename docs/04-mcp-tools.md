# 04 — Tools (data + channel adapters)

Tools are how agents reach the outside world: ocean/weather/satellite data in, messages out. Every tool is a **thin, dumb, single-attempt adapter** behind a uniform interface. All intelligence (retries, staleness, safety) lives elsewhere. Build every tool **mock-first**: a `MockAdapter` reads fixtures and works offline today; a `RealAdapter` sits beside it as a `# TODO(orca):` stub.

## 1. The tool interface & registry (`src/orca/tools/base.py`)

```python
from typing import Protocol, ClassVar
from pydantic import BaseModel
from orca.schemas import ToolResponse, SourceName

class ToolRequest(BaseModel):
    """Base request. Concrete tools subclass with their own fields."""
    pass

class Tool(Protocol):
    name: ClassVar[str]              # e.g. "incois_get_pfz"
    source: ClassVar[SourceName]
    def __call__(self, req: ToolRequest) -> ToolResponse: ...

# Simple registry so agents fetch tools by name and the mode (mock|real) is
# resolved centrally from config — agents never construct adapters themselves.
_REGISTRY: dict[str, Tool] = {}

def register(tool: Tool) -> Tool:
    _REGISTRY[tool.name] = tool
    return tool

def get_tool(name: str) -> Tool:
    return _REGISTRY[name]
```

Each concrete tool module defines **both** a mock and a real adapter and registers the one selected by `ORCA_DATA_MODE`:

```python
# pattern used in every tool module
from orca.config import settings

class _PFZMock:
    name = "incois_get_pfz"; source = SourceName.INCOIS_PFZ
    def __call__(self, req): ...        # reads fixtures/pfz/<cell>.geojson

class _PFZReal:
    name = "incois_get_pfz"; source = SourceName.INCOIS_PFZ
    def __call__(self, req):
        raise NotImplementedError  # TODO(orca): wire INCOIS PFZ endpoint (see §6)

register(_PFZReal() if settings.data_mode == "real" else _PFZMock())
```

**Contract for every adapter:**
- Exactly **one** fetch attempt. No retries inside the tool (that's `guardrails/resilience.py`).
- Never raise for "no data" or "remote failed" — return `ToolResponse(status=EMPTY|ERROR, …)`. Only truly exceptional bugs raise.
- Always stamp `retrieved_at = datetime.now(tz=UTC)` and set `source`.
- Numeric fields in the payload are `Measurement`s (unit + source + time baked in).
- Pure I/O only — no threshold logic, no LLM, no cross-source reasoning.

## 2. Data tools (MVP: mock-first)

### `tools/incois.py`

**`incois_get_pfz`** — Potential Fishing Zone advisory.
```python
class PFZRequest(ToolRequest):
    bbox: BoundingBox
    date: datetime | None = None      # default: latest advisory

class PFZPayload(BaseModel):
    nodes: list[PFZNode]              # each with location, depth (Measurement), valid_date
    advisory_id: str
    valid_from: datetime
    valid_to: datetime
```
Mock: loads `fixtures/pfz/<cell>.geojson` for the cell covering `bbox`, parses features into `PFZNode`s (`depth` → `Measurement(unit="m_depth", source=INCOIS_PFZ)`), returns `status=OK`; if no fixture, `status=EMPTY`.

**`incois_get_ocean_state`** — waves/currents/SST ocean-state forecast.
```python
class OceanStatePayload(BaseModel):
    wave_height: Measurement          # unit "m"
    swell_surge: Measurement | None   # unit "m"
    sst: Measurement | None           # unit "deg_c"
```

### `tools/imd.py`

**`imd_get_marine_warnings`** — marine weather + cyclone warnings. Real IMD/SACHET distributes these as **CAP-XML** alerts; model the payload on CAP so the real adapter is a parser swap, not a reshape.
```python
class MarineWarningPayload(BaseModel):
    wind_speed: Measurement                 # unit "kt"
    wave_height: Measurement | None         # unit "m"
    cyclone_distance: Measurement | None    # unit "km" (nearest active system)
    cap_event: str | None = None            # e.g. "Cyclonic Storm"
    cap_severity: str | None = None         # CAP severity verbatim (context only, NOT our verdict)
    headline: str | None = None
```
Note: `cap_severity` is carried for context only. **Our** go/no-go comes from `guardrails/thresholds.py`, never from the source's severity string.

### `tools/isro.py`

**`isro_get_chlorophyll`** — satellite EO (Oceansat OCM chlorophyll, SST). This is the ISRO-satellite story for the judges; keep it real in the mock.
```python
class ChlorophyllPayload(BaseModel):
    chlorophyll: Measurement          # unit "mg_m3"
    sst: Measurement | None           # unit "deg_c"
    sensor: str = "OCM"               # provenance detail
    granule_time: datetime            # satellite pass time → observed_at
```

### `tools/copernicus.py` — **scaffold only**
Historical reanalysis via NetCDF/xarray for the Ocean Analytics agent. Define `CopernicusRequest`/payload types; body `# TODO(orca): open NetCDF via xarray, subset by bbox/time`. Not reached by the two MVP intents.

## 3. Channel tools (outbound)

These send the composed answer back out. Same adapter discipline.

### `tools/channels/whatsapp.py`
**`whatsapp_send`** — POST to WhatsApp Cloud API `/messages`. Mock writes the payload to a log/return value so tests assert on it; real adapter uses `httpx` + `WHATSAPP_TOKEN`. Supports text now; voice-note upload is a `# TODO(orca):`.

### `tools/channels/ivr.py`
**`ivr_speak`** — hand TTS audio (or text for the telephony provider's TTS) back to Exotel/Twilio. Mock returns the would-be TwiML/response object; real adapter fills provider specifics.

## 4. How agents use tools (and how resilience wraps them)

Agents never call an adapter directly for anything safety-relevant. They go through the resilience wrapper so every fetch gets retries + breaker + freshness stamping in one place:

```python
# in an agent
from orca.tools.base import get_tool
from orca.guardrails.resilience import fetch   # wraps retry/backoff/breaker

resp = fetch(get_tool("imd_get_marine_warnings"), MarineWarningRequest(bbox=cell))
# `fetch` returns a ToolResponse and records data_freshness[source]=resp.retrieved_at
# on OK; on exhausted retries it returns status=ERROR (never raises into the agent).
```

See `docs/05-guardrails.md §resilience` for `fetch()`'s exact retry/backoff/circuit-breaker behavior. The division of labor: **tool = one honest attempt; resilience = policy; agent = what to do with the result.**

## 5. Fixtures the mocks read

Defined in `docs/03 §7`. Minimum set to ship the demo:
- `fixtures/pfz/calm_cell.geojson`, `fixtures/pfz/cyclone_cell.geojson`
- `fixtures/weather/calm_cell.json` (below thresholds), `fixtures/weather/cyclone_cell.json` (above thresholds)
- `fixtures/isro/calm_cell.json`, `fixtures/isro/cyclone_cell.json`
- `fixtures/geo/imbl.geojson`
- `fixtures/speech/*.json`

`scripts/seed_fixtures.py` writes these deterministically. The kill-a-source demo (docs/07) is done by pointing a tool at a missing/renamed fixture or setting a "force error" flag, so the mock returns `status=ERROR` and you watch the guardrail handle it.

## 6. Real-adapter reality (write these as TODO notes in the stubs, for whoever wires them later)

The MVP is mock-first for a real reason: these sources do **not** expose clean public JSON REST APIs. Record the honest integration path in each `RealAdapter` stub so v2 isn't a research project from zero:

- **INCOIS** — PFZ/ocean-state come via the INCOIS/ESSO portals and web/OGC map services and downloadable products, not a documented public REST/JSON API. Real adapter likely scrapes/parses a published product or uses an OGC (WMS/WFS) endpoint. `# TODO(orca): confirm INCOIS access method + terms of use.`
- **IMD / SACHET** — alerts are **CAP-XML** (Common Alerting Protocol). Real adapter fetches and parses CAP feeds. Our `MarineWarningPayload` already mirrors CAP fields. `# TODO(orca): subscribe/poll CAP feed; map CAP→payload.`
- **ISRO EO** — chlorophyll/SST products live on MOSDAC / Bhuvan / VEDAS as files/services (NetCDF/GeoTIFF), not a query API. `# TODO(orca): pull granule, subset by bbox, extract value.`
- **Copernicus Marine** — has a proper toolbox/API and NetCDF; the cleanest real integration, hence the xarray scaffold. `# TODO(orca): CMEMS credentials + subset request.`
- **Bhashini** — real ASR/translation/TTS via the ULCA pipeline API (see `speech/bhashini.py`). `# TODO(orca): auth + pipeline config IDs.`

Marking these accurately is part of the deliverable: it shows the judges (and the future implementer) that the mock boundary was chosen deliberately and the real path is understood.
