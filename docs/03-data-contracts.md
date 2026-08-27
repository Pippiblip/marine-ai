# 03 — Data contracts

These are the exact types. Put the shared ones in `src/orca/schemas.py` and the graph state in `src/orca/state.py`. Everything crossing a module boundary is one of these Pydantic models — never a bare `dict`. Types here are the source of truth; if a diagram elsewhere is looser, this wins.

## 1. Provenance is built into every datum

The single most important design rule: **every value carries where it came from and when.** This is what makes the guardrail and the "cite your source" behavior possible. So we don't pass around raw floats — we pass `Measurement`s.

```python
# src/orca/schemas.py
from datetime import datetime
from enum import Enum
from typing import Literal, Any
from pydantic import BaseModel, Field

class SourceName(str, Enum):
    INCOIS_PFZ = "incois_pfz"
    INCOIS_OCEAN_STATE = "incois_ocean_state"
    IMD_MARINE = "imd_marine"
    ISRO_CHLOROPHYLL = "isro_chlorophyll"
    COPERNICUS = "copernicus"          # scaffold
    MOCK = "mock"

class Measurement(BaseModel):
    """A single value bound to its origin and time. The unit is explicit."""
    value: float
    unit: str                          # "m", "kt", "km", "deg_c", "mg_m3", "m_depth"
    source: SourceName
    retrieved_at: datetime             # when the tool successfully fetched it
    observed_at: datetime | None = None  # when the reading itself was taken, if known
    def age_seconds(self, now: datetime) -> float:
        return (now - self.retrieved_at).total_seconds()
```

Rule for the whole codebase: **if a number will ever reach the user, it is a `Measurement`.** The Synthesis agent may only speak values that exist as `Measurement`s in state (enforced by `guardrails/provenance.py`).

## 2. Geospatial primitives

```python
class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class PFZNode(BaseModel):
    """A candidate fishing zone from INCOIS PFZ advisory."""
    location: GeoPoint
    depth: Measurement | None = None          # bathymetry, unit "m_depth"
    bearing_deg: float | None = None          # filled by Geospatial agent
    distance_km: Measurement | None = None    # filled by Geospatial agent
    valid_date: datetime                      # advisory validity
```

## 3. Safety flags (only the Weather & Risk agent may create these)

```python
class Severity(str, Enum):
    INFO = "info"
    ADVISORY = "advisory"
    WARNING = "warning"
    DANGER = "danger"          # go/no-go = NO

class SafetyFlag(BaseModel):
    code: str                  # "high_wave", "high_wind", "cyclone_proximity", "swell_surge", "imbl_proximity"
    severity: Severity
    message_key: str           # key into guardrails/templates.py (NOT free LLM text)
    triggered_by: list[Measurement]   # the exact readings that tripped the rule
    threshold_repr: str        # human string of the rule, e.g. "wave_height > 2.5 m"
```

`triggered_by` binds the flag to the readings that caused it — the guardrail and synthesis both rely on this so the spoken warning can name the number and its time.

## 4. Specialist result types

Each specialist writes exactly one of these into state. Note they hold `Measurement`s, not floats.

```python
class MarineDataResult(BaseModel):
    pfz_nodes: list[PFZNode]
    chlorophyll: Measurement | None = None    # ISRO OCM, unit "mg_m3" (for the EO story)
    sst: Measurement | None = None            # sea-surface temp, unit "deg_c"
    source_freshness: dict[SourceName, datetime]

class WeatherRiskResult(BaseModel):
    wave_height: Measurement | None = None
    wind_speed: Measurement | None = None
    cyclone_distance: Measurement | None = None
    swell_surge: Measurement | None = None
    safety_flags: list[SafetyFlag] = []       # appended by this agent ONLY
    source_freshness: dict[SourceName, datetime]

class GeospatialResult(BaseModel):
    nearest_pfz: PFZNode | None = None
    distance_km: Measurement | None = None
    bearing_deg: float | None = None
    inside_imbl_buffer: bool | None = None    # True if within warning buffer of the boundary
    imbl_distance_km: Measurement | None = None

class OceanAnalyticsResult(BaseModel):   # scaffold / v2
    observation: str | None = None       # stated as observation, never invented causation
    series: list[Measurement] = []
```

## 5. The shared graph state

```python
# src/orca/state.py
from datetime import datetime
from typing import TypedDict, Literal
from orca.schemas import (GeoPoint, SafetyFlag, MarineDataResult,
                          WeatherRiskResult, GeospatialResult, OceanAnalyticsResult, SourceName)

class PlatformState(TypedDict, total=False):
    # --- set by Channel Gateway ---
    query_text: str                  # transcribed AND translated to English
    source_lang: str                 # e.g. "ta-IN", "hi-IN", "en-IN"
    channel: Literal["web", "whatsapp", "ivr"]
    user_location: GeoPoint | None
    trace_id: str                    # per-run id for logging

    # --- set by Router ---
    intent: str                      # "pfz_nearest" | "safety_check" | ...
    subtasks: list[str]              # agent node names to run

    # --- set by specialists (each writes only its own slice) ---
    marine_data_result: MarineDataResult | None
    weather_risk_result: WeatherRiskResult | None
    geospatial_result: GeospatialResult | None
    ocean_analytics_result: OceanAnalyticsResult | None   # scaffold

    # --- safety + freshness (the two fields Synthesis MUST check) ---
    safety_flags: list[SafetyFlag]
    data_freshness: dict[SourceName, datetime]   # source -> last successful fetch time

    # --- set by Guardrail ---
    guardrail_status: Literal["ok", "stale", "failed"]
    guardrail_notes: list[str]       # machine reasons, for logging + template selection

    # --- set by Synthesis ---
    final_response_text: str         # the English answer actually spoken (post-guardrail)
    response_lang_text: str          # final_response_text translated back to source_lang
    citations: list[str]             # e.g. ["INCOIS PFZ advisory @ 2026-09-20 06:00 IST"]
```

**Contract rules on state:**
- A node reads any field but **writes only its designated slice** (see each `agents/*.md`). No overwrites.
- `safety_flags` is append-only, and **only** `weather_risk` appends to it; the guardrail may *reorder/validate* but not fabricate.
- `data_freshness[source]` is set whenever a tool returns successfully; the guardrail reads it.
- `guardrail_status` gates Synthesis: `ok` → normal answer; `stale` → answer with an explicit "as of [time]" + caution; `failed` → the explicit-failure template, no invented values.

## 6. Tool request/response contracts

Every tool takes a typed request and returns a typed response whose numeric fields are `Measurement`s. Full per-tool detail in `docs/04-mcp-tools.md`; the shared shape:

```python
class BoundingBox(BaseModel):
    min_lat: float; min_lon: float; max_lat: float; max_lon: float

class ToolStatus(str, Enum):
    OK = "ok"
    EMPTY = "empty"          # query ran, no data for this area/time
    ERROR = "error"          # fetch failed (after the adapter's own attempt)

class ToolResponse(BaseModel):
    status: ToolStatus
    retrieved_at: datetime
    source: SourceName
    payload: BaseModel | None      # a source-specific model (PFZ list, warnings, …)
    error: str | None = None
```

The **guardrail/resilience layer** — not the tool — owns retries, backoff, and the circuit breaker. A tool adapter does one fetch attempt and reports `OK`/`EMPTY`/`ERROR`; `guardrails/resilience.py` wraps the call with the 3-attempt backoff and breaker. This keeps tools dumb and the safety logic in one auditable place.

## 7. Fixtures (mock data format)

Fixtures live under `src/orca/fixtures/` and are plain JSON/GeoJSON so they're diff-able and demo-stable. Each mock adapter loads the fixture matching the request (by bounding box / cell id / date) and stamps `retrieved_at = now()`.

- `fixtures/pfz/<cell>.geojson` — FeatureCollection of PFZ points with `depth_m`, `valid_date`.
- `fixtures/weather/<cell>.json` — `{wave_height_m, wind_speed_kt, cyclone_distance_km, swell_surge_m, observed_at}`.
- `fixtures/weather/<cell>__CYCLONE.json` — a variant with values **above** the thresholds, for the safety demo.
- `fixtures/geo/imbl.geojson` — the India–Sri Lanka IMBL as a LineString/Polygon buffer for geofencing (a simplified but plausible boundary is fine for the demo; mark `# TODO(orca): replace with official IMBL shapefile`).
- `fixtures/isro/<cell>.json` — chlorophyll (`mg_m3`) + SST (`deg_c`) for the EO visual/story.
- `fixtures/speech/*.json` — canned `{lang, transcript}` for `MockSpeech.asr`, keyed by an audio id the web client sends.

Provide at least two cells: one **calm** (safe → normal answer) and one **cyclone** (unsafe → red alert). `scripts/seed_fixtures.py` (re)generates them. The demo in `docs/07` depends on these existing and being deterministic.
