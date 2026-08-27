# Agent 05 — Geospatial Reasoning

> File: `src/orca/agents/geospatial.py` · Node: `geospatial` · MVP: build fully. Runs for `pfz_nearest`, `safety_check`, `boundary_check`.

## Job
Do the spatial math: which PFZ node is nearest (distance + bearing from the user), and is the user near a maritime boundary (IMBL). Pure deterministic geometry — **no LLM here.** This agent turns lat/lon into the numbers the answer needs.

## State I/O
**Writes:** `geospatial_result: GeospatialResult` (nearest PFZ, distance `Measurement`, bearing, IMBL proximity).
**Reads:** `user_location`, `marine_data_result` (for candidate PFZ nodes).

## Tools / dependencies
- `geo/distance.py` — `haversine(a, b)`, `bearing(a, b)`. Hand-rolled and unit-tested.
- `geo/geofence.py` — point-in-polygon / distance-to-line against `fixtures/geo/imbl.geojson` (shapely).
- No external data tools (it consumes what marine_data already fetched).

## Algorithm
1. If `user_location is None`: write an empty result and let Synthesis raise `location_unknown`. Do not assume a location.
2. For `pfz_nearest`: over `marine_data_result.pfz_nodes`, compute haversine distance from `user_location` to each; pick the min. Fill `nearest_pfz`, `distance_km` (`Measurement`, unit `km`, source = the PFZ's source), `bearing_deg`. Also set `distance_km`/`bearing_deg` on the chosen `PFZNode`.
3. For IMBL: compute distance from `user_location` to the boundary; set `inside_imbl_buffer` (True if within a warning buffer, e.g. 5 km) and `imbl_distance_km`.
4. Write `GeospatialResult`.

## Guardrail interactions
- Distances/bearings it emits are `Measurement`s so they pass provenance and appear in citations.
- `inside_imbl_buffer=True` is advisory context for Synthesis (an "you are near the maritime boundary" note); it does **not** itself create a `SafetyFlag` (only weather_risk does). If boundary proximity should escalate, that's a `# TODO(orca):` future rule in `thresholds.py`, not ad-hoc here.
- Deterministic and offline — heavily unit-tested (see `test_geo_*`).

## Acceptance test
`test_agents_geospatial.py`: given the calm cell's PFZ nodes and a known user point, selects the correct nearest node with distance/bearing within tolerance; a point inside the IMBL buffer sets `inside_imbl_buffer=True`; `user_location=None` yields an empty result without crashing.
