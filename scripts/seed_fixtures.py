#!/usr/bin/env python3
"""Write the deterministic demo fixtures under src/orca/fixtures/."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "orca" / "fixtures"


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    """Regenerate calm/cyclone cells and speech fixture metadata."""
    _write(
        ROOT / "weather" / "calm.json",
        {
            "observed_at": "2026-09-20T05:30:00+00:00",
            "wind_speed_kt": 18.0,
            "wave_height_m": 1.6,
            "cyclone_distance_km": 420.0,
            "swell_surge_m": 0.8,
            "sst_deg_c": 29.1,
            "headline": "Moderate sea state",
            "cap_event": "small_craft_alert",
            "cap_severity": "moderate",
        },
    )
    _write(
        ROOT / "weather" / "cyclone.json",
        {
            "observed_at": "2026-09-20T05:30:00+00:00",
            "wind_speed_kt": 32.0,
            "wave_height_m": 3.4,
            "cyclone_distance_km": 180.0,
            "swell_surge_m": 2.4,
            "sst_deg_c": 28.4,
            "headline": "Cyclonic storm — high seas",
            "cap_event": "Cyclonic Storm",
            "cap_severity": "extreme",
        },
    )
    _write(
        ROOT / "isro" / "calm.json",
        {
            "observed_at": "2026-09-20T05:15:00+00:00",
            "chlorophyll_mg_m3": 1.4,
            "sst_deg_c": 29.2,
            "sensor": "OCM",
        },
    )
    _write(
        ROOT / "isro" / "cyclone.json",
        {
            "observed_at": "2026-09-20T05:15:00+00:00",
            "chlorophyll_mg_m3": 0.6,
            "sst_deg_c": 28.4,
            "sensor": "OCM",
        },
    )
    _write(
        ROOT / "speech" / "pfz_query_en.json",
        {"lang": "en-IN", "transcript": "Where is the nearest fishing zone today?"},
    )
    _write(
        ROOT / "speech" / "safety_query_en.json",
        {"lang": "en-IN", "transcript": "Is it safe to go out tomorrow morning?"},
    )
    print(f"Wrote fixtures under {ROOT}")


if __name__ == "__main__":
    main()
