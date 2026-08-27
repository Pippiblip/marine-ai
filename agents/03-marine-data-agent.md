# Agent 03 — Marine Data Discovery

> File: `src/orca/agents/marine_data.py` · Node: `marine_data` · MVP: build fully. Runs for `pfz_nearest`.

## Job
Find the fishing-relevant data for the user's area: Potential Fishing Zones (INCOIS PFZ) plus the satellite EO signals that make the answer credible (ISRO chlorophyll, SST). It retrieves and packages; it does not compute distances (that's Geospatial) or judge safety (that's Weather & Risk).

## State I/O
**Writes:** `marine_data_result: MarineDataResult` (PFZ nodes, chlorophyll, SST, `source_freshness`).
**Reads:** `user_location`, `intent`.

## Tools / dependencies
- `incois_get_pfz` → `PFZPayload` (nodes with depth + validity).
- `isro_get_chlorophyll` → `ChlorophyllPayload` (chlorophyll `mg_m3`, SST, sensor, `granule_time`).
- All via `resilience.fetch(get_tool(...), req, freshness=state["data_freshness"])` so freshness is recorded and failures don't raise.

## Algorithm
1. Build a `BoundingBox` around `user_location` (small cell, e.g. ±0.25°).
2. `fetch` PFZ; map payload nodes into `PFZNode`s (depth as `Measurement`). If `EMPTY`, keep `pfz_nodes=[]` (Synthesis will say "no advisory for your area today" — not a guess).
3. `fetch` ISRO chlorophyll/SST; attach as `Measurement`s (source `ISRO_CHLOROPHYLL`, `observed_at=granule_time`).
4. Assemble `MarineDataResult`; populate `source_freshness` for each source that returned `OK`.

## Guardrail interactions
- Does **not** set `safety_flags`. Does not filter by distance.
- On tool `ERROR`, record nothing for that source (its absence from `data_freshness` is what the guardrail keys on). Never fabricate a PFZ node.
- Every numeric it stores is a `Measurement` so provenance/citations work downstream.

## Acceptance test
`test_agents_marine_data.py`: for the calm cell, returns ≥1 `PFZNode` with a depth `Measurement` and a chlorophyll `Measurement`, and sets `source_freshness` for both sources; for an unknown cell, returns empty `pfz_nodes` without error.
