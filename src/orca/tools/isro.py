"""ISRO chlorophyll and SST mock adapters."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from orca.config import settings
from orca.schemas import Measurement, SourceName, ToolResponse, ToolStatus
from orca.tools.base import ToolRequest, register


class ChlorophyllRequest(ToolRequest):
    """Request chlorophyll and SST data for a location."""

    cell_id: Optional[str] = None
    force_error: bool = False


class ChlorophyllPayload(BaseModel):
    """Result of an ISRO EO query."""

    chlorophyll: Measurement
    sst: Measurement
    sensor: str = "OCM"
    granule_time: datetime = datetime.now(timezone.utc)


class ISROChlorophyllMock:
    """Mock ISRO adapter backed by deterministic fixture files."""

    name = "isro_get_chlorophyll"
    source = SourceName.ISRO_CHLOROPHYLL

    def __call__(self, req: ChlorophyllRequest) -> ToolResponse:
        """Return the fixture-backed ocean-colour response for a request."""
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
            / "isro"
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

        payload = ChlorophyllPayload(
            chlorophyll=Measurement(
                value=float(data["chlorophyll_mg_m3"]),
                unit="mg_m3",
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                observed_at=datetime.fromisoformat(data["observed_at"]),
            ),
            sst=Measurement(
                value=float(data["sst_deg_c"]),
                unit="deg_c",
                source=self.source,
                retrieved_at=datetime.now(timezone.utc),
                observed_at=datetime.fromisoformat(data["observed_at"]),
            ),
            sensor=data.get("sensor", "OCM"),
            granule_time=datetime.fromisoformat(data["observed_at"]),
        )

        return ToolResponse(
            status=ToolStatus.OK,
            source=self.source,
            retrieved_at=datetime.now(timezone.utc),
            payload=payload,
        )


class ISROChlorophyllReal:
    """Real ISRO adapter stub."""

    name = "isro_get_chlorophyll"
    source = SourceName.ISRO_CHLOROPHYLL

    def __call__(self, req: ChlorophyllRequest) -> ToolResponse:
        """Raise until the live ISRO adapter is implemented."""
        # TODO(orca): pull MOSDAC/Bhuvan granule, subset by bbox, extract chlorophyll/SST.
        raise NotImplementedError("TODO(orca): wire ISRO EO product fetch")


register(ISROChlorophyllReal() if settings.data_mode == "real" else ISROChlorophyllMock())
