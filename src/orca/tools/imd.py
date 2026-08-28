"""IMD marine warning mock adapters."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from orca.config import settings
from orca.schemas import Measurement, SourceName, ToolResponse, ToolStatus
from orca.tools.base import ToolRequest, register


class MarineWarningRequest(ToolRequest):
    """Request marine warning data for a cell or region."""

    cell_id: Optional[str] = None
    force_error: bool = False


class MarineWarningPayload(BaseModel):
    """Result of an IMD marine warning query."""

    wind_speed: Measurement
    wave_height: Optional[Measurement] = None
    cyclone_distance: Optional[Measurement] = None
    swell_surge: Optional[Measurement] = None
    cap_event: Optional[str] = None
    cap_severity: Optional[str] = None
    headline: Optional[str] = None


class IMDMarineWarningsMock:
    """Mock IMD adapter for marine warning fixture data."""

    name = "imd_get_marine_warnings"
    source = SourceName.IMD_MARINE

    def __call__(self, req: MarineWarningRequest) -> ToolResponse:
        """Return the fixture-backed warning response for a request."""
        if req.force_error:
            return ToolResponse(
                status=ToolStatus.ERROR,
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                payload=None,
                error="forced_error",
            )

        cell_id = req.cell_id or "calm"
        fixture_path = (
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "weather"
            / f"{cell_id}.json"
        )

        if not fixture_path.exists():
            return ToolResponse(
                status=ToolStatus.EMPTY,
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                payload=None,
            )

        with open(fixture_path, encoding="utf-8") as fh:
            data = json.load(fh)

        payload = MarineWarningPayload(
            wind_speed=Measurement(
                value=float(data["wind_speed_kt"]),
                unit="kt",
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                observed_at=datetime.fromisoformat(data["observed_at"]),
            ),
            wave_height=Measurement(
                value=float(data["wave_height_m"]),
                unit="m",
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                observed_at=datetime.fromisoformat(data["observed_at"]),
            ),
            cyclone_distance=Measurement(
                value=float(data["cyclone_distance_km"]),
                unit="km",
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                observed_at=datetime.fromisoformat(data["observed_at"]),
            )
            if "cyclone_distance_km" in data
            else None,
            swell_surge=Measurement(
                value=float(data["swell_surge_m"]),
                unit="m",
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                observed_at=datetime.fromisoformat(data["observed_at"]),
            )
            if "swell_surge_m" in data
            else None,
            cap_event=data.get("cap_event"),
            cap_severity=data.get("cap_severity"),
            headline=data.get("headline"),
        )

        return ToolResponse(
            status=ToolStatus.OK,
            source=self.source,
            retrieved_at=datetime.now(timezone.utc),
            payload=payload,
        )


class IMDMarineWarningsReal:
    """Real IMD adapter stub."""

    name = "imd_get_marine_warnings"
    source = SourceName.IMD_MARINE

    def __call__(self, req: MarineWarningRequest) -> ToolResponse:
        """Raise until the live IMD adapter is implemented."""
        # TODO(orca): subscribe/poll IMD/SACHET CAP-XML feed; map CAP→payload.
        raise NotImplementedError("TODO(orca): wire IMD CAP feed parser")


register(IMDMarineWarningsReal() if settings.data_mode == "real" else IMDMarineWarningsMock())
