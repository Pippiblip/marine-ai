"""Copernicus Marine historical reanalysis — scaffold only."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel

from orca.config import settings
from orca.schemas import BoundingBox, Measurement, SourceName, ToolResponse, ToolStatus
from orca.tools.base import ToolRequest, register


class CopernicusRequest(ToolRequest):
    """Subset request for a Copernicus Marine product."""

    bbox: Optional[BoundingBox] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class CopernicusPayload(BaseModel):
    """Historical series extracted from a NetCDF subset."""

    series: list[Measurement]


class CopernicusMock:
    """Scaffold mock — not used by MVP intents."""

    name = "copernicus_get_reanalysis"
    source = SourceName.COPERNICUS

    def __call__(self, req: CopernicusRequest) -> ToolResponse:
        """Return empty until Ocean Analytics is implemented."""
        # TODO(orca): open NetCDF via xarray, subset by bbox/time.
        return ToolResponse(
            status=ToolStatus.EMPTY,
            source=self.source,
            retrieved_at=datetime.now(timezone.utc),
            payload=None,
        )


class CopernicusReal:
    """Real Copernicus Marine adapter stub."""

    name = "copernicus_get_reanalysis"
    source = SourceName.COPERNICUS

    def __call__(self, req: CopernicusRequest) -> ToolResponse:
        """Raise until CMEMS credentials and subsetting are wired."""
        # TODO(orca): CMEMS credentials + subset request.
        raise NotImplementedError("TODO(orca): wire Copernicus Marine toolbox/API")


register(CopernicusReal() if settings.data_mode == "real" else CopernicusMock())
