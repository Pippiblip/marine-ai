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

**Current Milestone: M2 — Deterministic core** ✅

| Milestone | Status | Summary |
|-----------|--------|---------|
| M0 | ✅ Done | Skeleton, config, `/health` endpoint |
| M1 | ✅ Done | Contracts, interfaces, mock LLM/speech |
| M2 | ✅ Done | Deterministic geo math and fully tested guardrails |
| M3 | ⏳ TODO | Tools, fixtures (mock adapters) |
| M4 | ⏳ TODO | Agents, graph (end-to-end `pfz_nearest`) |
| M5 | ⏳ TODO | Safety path, failure behavior |
| M6 | ⏳ TODO | Channels, web client |
| M7 | ⏳ TODO | MCP exposure (optional) |
| M8 | ⏳ TODO | Hardening, demo polish |

### M2 completion record

M2 is the deterministic spine of ORCA. It takes structured measurements and
coordinates as input and produces distances, safety flags, freshness decisions,
failure states, and fixed messages without calling an LLM or a network service.

#### Deterministic geospatial math

All `GeoPoint` values are validated latitude/longitude pairs. GeoJSON polygon
coordinates are read in `(longitude, latitude)` order, while `GeoPoint` exposes
`lat` and `lon` fields. The implementation keeps that conversion explicit so a
latitude cannot accidentally be treated as a longitude.

**1. Great-circle distance**

`haversine_km(p1, p2)` converts both points to radians and computes the shortest
surface distance over a spherical Earth. With latitude difference $d_{lat}$,
longitude difference $d_{lon}$, and $R = 6371.0$ km:

$$
a = \sin^2\left(\frac{\Delta\phi}{2}\right) +
\cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)
$$

$$
c = 2\arcsin(\sqrt{\min(1,a)}), \qquad d = R c
$$

The `min(1, a)` clamp protects `asin` from a tiny floating-point overshoot at
coincident or antipodal points. The result is a plain `float` in kilometers;
when it is returned to a user elsewhere in ORCA, it must be wrapped in a
provenance-carrying `Measurement`.

**2. Initial compass bearing**

`bearing_deg(p1, p2)` computes the initial true-north bearing, rather than a
flat-map angle. After converting coordinates to radians:

$$
y = \sin(\Delta\lambda)\cos(\phi_2)
$$

$$
x = \cos(\phi_1)\sin(\phi_2) -
\sin(\phi_1)\cos(\phi_2)\cos(\Delta\lambda)
$$

$$
theta = atan2(y, x) * 180 / pi
$$

The result is normalized with `(theta + 360) % 360`, giving north as 0,
east as 90, south as 180, and west as 270. This is used with Haversine
distance when selecting and describing a nearest PFZ node.

**3. Point-in-polygon containment**

`point_in_polygon()` uses ray casting. It projects a horizontal ray from the
test point and toggles an `inside` boolean every time the ray crosses a polygon
edge. Horizontal edges are skipped by the crossing rules, and points exactly
on an edge are explicitly treated as inside. Rings with fewer than three points
return `False` instead of raising.

**4. Distance to an IMBL polygon boundary**

`closest_distance_to_polygon_km()` checks every edge, including the closing edge
from the last coordinate back to the first. For the short local distances used
by the demo, it projects the coordinates around the query point into kilometers:

$$
x = (\operatorname{lon} - \operatorname{lon}_p) \times
111.32\cos(\operatorname{lat}_p), \qquad
y = (\operatorname{lat} - \operatorname{lat}_p) \times 111.32
$$

For each segment from $A$ to $B$, it projects the origin onto the segment and
clamps the projection parameter to $[0,1]$:

$$
t = \operatorname{clamp}\left(
$$

The candidate boundary distance is the smallest Euclidean distance to
$A + t(B-A)$. `is_near_imbl_buffer()` returns `(is_near, distance_km)` when
that distance is at most `buffer_km`. It checks proximity to the boundary,
not polygon interior containment; the two decisions are tested separately.

This is a deterministic local approximation, not an official geodesic GIS
operation. The checked demo area is small and the approach is auditable. The
official IMBL geometry and production-grade geodesic treatment remain future
work, marked in the roadmap.

#### Deterministic guardrail flow

1. `thresholds.evaluate()` compares each optional weather measurement with its
      configured boundary. Wave and wind values trigger `DANGER` only when strictly
      above their limits; cyclone distance triggers `DANGER` strictly below its
      limit; swell triggers `WARNING` strictly above its limit. Exact boundaries
      are therefore documented and tested as non-triggering.
2. Each flag stores the exact triggering `Measurement`, a stable `message_key`,
      severity, and a textual `threshold_repr`. The LLM cannot create or override
      these flags.
3. `freshness.is_fresh()` compares measurement age against the configured
      safety or PFZ window. `caption()` always emits the retrieval timestamp and
      age, so fresh data is still time-qualified rather than presented as timeless.
4. `resilience.fetch()` checks the source breaker, performs up to three attempts,
      waits using the configured backoff sequence `(0.0, 0.5, 1.5)` seconds, and
      converts adapter exceptions into `ERROR` responses. `EMPTY` is returned
      immediately because it is a valid no-data result. Three failed fetch cycles
      open that source's breaker for 60 seconds; a successful response resets it
      and records its retrieval time in the freshness map.
5. `provenance.verify()` extracts numeric tokens from a draft and compares them
      with measurement values plus sensible integer rounding. ISO dates and clock
      times are treated as citation metadata; every other number must be backed by
      a measurement or the draft is rejected. This now handles signed and
      scientific-notation values as well.
6. `templates.render()` provides fixed literal language for danger, warning,
      stale, partial, unavailable, all-clear, and missing-location states. An
      unknown message key raises an error rather than silently producing text.

The M2 tests are offline and use injected clocks/sleeps for deterministic
resilience checks. They cover threshold boundaries and combined flags, both
freshness windows, retry and breaker behavior, provenance violations and
rounding, all templates, known distance/bearing pairs, polygon edge cases,
the default IMBL fixture, and buffer distances.

Deferred to later milestones: replacing the simplified demo IMBL GeoJSON with the
official boundary and adapter-facing integration (M3), graph guardrail-node wiring and cached last-known readings (M4/M5),
and tool/agent/channel behavior (M3-M6). No live source integration is part of M2.


## Golden Rules

This is safety-critical software. To ensure trustworthiness, we enforce seven rules:

1. **The LLM never invents a number.** Every wave height, wind speed, or coordinate must come from a tool response or deterministic code.
2. **Safety verdicts are hard-coded, not the LLM.** Thresholds are immutable Python; the model narrates, it doesn't decide.
3. **Every number carries provenance.** Timestamp, source, observation time — all baked in.
4. **Mock-first.** All tools read fixtures by default; real adapters are stubs.
5. **Provider-agnostic AI.** LLM and speech go through interfaces, not vendor SDKs.
6. **Scope discipline.** MVP fully built, everything else scaffolded with `# TODO(orca):`.
7. **Determinism in code, language in the LLM.** Math and safety logic are pure, tested Python; only narration and translation touch the model.


## Roadmap (v2 & beyond)

🟡 **Scaffolded for future work** (stubs in place, not fully built):

🔴 **Out of scope** (noted for reference, not built):


## License

MIT License. See `LICENSE` file for details.


## Contributing

This is an active hackathon project. Contributions welcome; follow the structure in `AGENTS.md` and `docs/`.


## Questions?

See the specification:
