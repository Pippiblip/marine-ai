"""INCOIS PFZ and ocean-state mock adapters."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from orca.config import settings
from orca.schemas import (
    BoundingBox,
    GeoPoint,
    Measurement,
    PFZNode,
    SourceName,
    ToolResponse,
    ToolStatus,
)
from orca.tools.base import ToolRequest, register


class PFZRequest(ToolRequest):
    """Request a PFZ advisory for a known cell or bounding box."""

    cell_id: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    date: Optional[datetime] = None
    force_error: bool = False


class PFZPayload(BaseModel):
    """Result of a PFZ query."""

    nodes: list[PFZNode] = Field(default_factory=list)
    advisory_id: str = "pfz-demo"
    valid_from: datetime = datetime.now(timezone.utc)
    valid_to: datetime = datetime.now(timezone.utc)


class IncoisPFZMock:
    """Mock INCOIS adapter that reads PFZ fixture data."""

    name = "incois_get_pfz"
    source = SourceName.INCOIS_PFZ

    def __call__(self, req: PFZRequest) -> ToolResponse:
        """Return the fixture-backed PFZ response for a request."""
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
            Path(__file__).resolve().parents[1] / "fixtures" / "pfz" / f"{cell_id}.geojson"
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

        nodes: list[PFZNode] = []
        for feature in data.get("features", []):
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [0, 0])
            lon, lat = coords
            depth_value = feature.get("properties", {}).get("depth_m", 20.0)
            valid_date = feature.get("properties", {}).get("valid_date")
            nodes.append(
                PFZNode(
                    location=GeoPoint(lat=float(lat), lon=float(lon)),
                    depth=Measurement(
                        value=float(depth_value),
                        unit="m_depth",
                        source=self.source,
                        retrieved_at=datetime.now(timezone.utc),
                    ),
                    valid_date=datetime.fromisoformat(valid_date)
                    if valid_date
                    else datetime.now(timezone.utc),
                )
            )

        payload = PFZPayload(
            nodes=nodes,
            valid_from=datetime.now(timezone.utc),
            valid_to=datetime.now(timezone.utc),
        )
        return ToolResponse(
            status=ToolStatus.OK,
            source=self.source,
            retrieved_at=datetime.now(timezone.utc),
            payload=payload,
        )


class IncoisPFZReal:
    """Real INCOIS adapter stub."""

    name = "incois_get_pfz"
    source = SourceName.INCOIS_PFZ

    def __call__(self, req: PFZRequest) -> ToolResponse:
        """Raise until the live INCOIS adapter is implemented."""
        # TODO(orca): confirm INCOIS access method + terms of use; PFZ is portal/OGC, not REST JSON.
        raise NotImplementedError("TODO(orca): wire live INCOIS PFZ endpoint")


class OceanStateRequest(ToolRequest):
    """Request INCOIS ocean-state for a cell."""

    cell_id: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    force_error: bool = False


class OceanStatePayload(BaseModel):
    """Waves, swell, and SST from the ocean-state product."""

    wave_height: Measurement
    swell_surge: Optional[Measurement] = None
    sst: Optional[Measurement] = None


def _weather_fixture_path(cell_id: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "weather" / f"{cell_id}.json"


class IncoisOceanStateMock:
    """Mock ocean-state adapter sharing the weather fixture files."""

    name = "incois_get_ocean_state"
    source = SourceName.INCOIS_OCEAN_STATE

    def __call__(self, req: OceanStateRequest) -> ToolResponse:
        """Return fixture-backed ocean-state for a request."""
        if req.force_error:
            return ToolResponse(
                status=ToolStatus.ERROR,
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                payload=None,
                error="forced_error",
            )
        cell_id = req.cell_id or "calm"
        fixture_path = _weather_fixture_path(cell_id)
        if not fixture_path.exists():
            return ToolResponse(
                status=ToolStatus.EMPTY,
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                payload=None,
            )
        with open(fixture_path, encoding="utf-8") as fh:
            data = json.load(fh)
        now = datetime.now(timezone.utc)
        observed = datetime.fromisoformat(data["observed_at"])
        swell = data.get("swell_surge_m")
        sst = data.get("sst_deg_c")
        payload = OceanStatePayload(
            wave_height=Measurement(
                value=float(data["wave_height_m"]),
                unit="m",
                source=self.source,
                retrieved_at=now,
                observed_at=observed,
            ),
            swell_surge=(
                Measurement(
                    value=float(swell),
                    unit="m",
                    source=self.source,
                    retrieved_at=now,
                    observed_at=observed,
                )
                if swell is not None
                else None
            ),
            sst=(
                Measurement(
                    value=float(sst),
                    unit="deg_c",
                    source=self.source,
                    retrieved_at=now,
                    observed_at=observed,
                )
                if sst is not None
                else None
            ),
        )
        return ToolResponse(
            status=ToolStatus.OK,
            source=self.source,
            retrieved_at=now,
            payload=payload,
        )


class IncoisOceanStateReal:
    """Real INCOIS ocean-state adapter stub."""

    name = "incois_get_ocean_state"
    source = SourceName.INCOIS_OCEAN_STATE

    def __call__(self, req: OceanStateRequest) -> ToolResponse:
        """Raise until the live ocean-state product is wired."""
        # TODO(orca): confirm INCOIS access method + terms of use; parse published product.
        raise NotImplementedError("TODO(orca): wire live INCOIS ocean-state endpoint")


register(IncoisPFZReal() if settings.data_mode == "real" else IncoisPFZMock())
register(IncoisOceanStateReal() if settings.data_mode == "real" else IncoisOceanStateMock())
