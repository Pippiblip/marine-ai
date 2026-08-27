"""
All shared Pydantic models for ORCA.

These models cross module boundaries; everything flowing between systems is
typed via one of these classes. Never pass bare dicts.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceName(str, Enum):
    """Data source identifier."""

    INCOIS_PFZ = "incois_pfz"
    INCOIS_OCEAN_STATE = "incois_ocean_state"
    IMD_MARINE = "imd_marine"
    ISRO_CHLOROPHYLL = "isro_chlorophyll"
    COPERNICUS = "copernicus"
    MOCK = "mock"


class Measurement(BaseModel):
    """A single value bound to its origin and time.

    The unit is explicit. Every number that reaches the user must be a
    Measurement so provenance is always available.
    """

    value: float
    unit: str  # "m", "kt", "km", "deg_c", "mg_m3", "m_depth"
    source: SourceName
    retrieved_at: datetime  # when the tool successfully fetched it
    observed_at: Optional[datetime] = None  # when the reading was taken, if known

    def age_seconds(self, now: datetime) -> float:
        """Return age of this measurement in seconds."""
        return (now - self.retrieved_at).total_seconds()


class GeoPoint(BaseModel):
    """A geographic point."""

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class PFZNode(BaseModel):
    """A candidate fishing zone from INCOIS PFZ advisory."""

    location: GeoPoint
    depth: Optional[Measurement] = None  # bathymetry, unit "m_depth"
    bearing_deg: Optional[float] = None  # filled by Geospatial agent
    distance_km: Optional[Measurement] = None  # filled by Geospatial agent
    valid_date: datetime  # advisory validity


class Severity(str, Enum):
    """Safety flag severity levels."""

    INFO = "info"
    ADVISORY = "advisory"
    WARNING = "warning"
    DANGER = "danger"  # go/no-go = NO


class SafetyFlag(BaseModel):
    """A deterministic safety alert raised by Weather & Risk Agent only."""

    code: str  # "high_wave", "high_wind", "cyclone_proximity", "swell_surge"
    severity: Severity
    message_key: str  # key into guardrails/templates.py (NOT free LLM text)
    triggered_by: List[Measurement]  # the exact readings that tripped the rule
    threshold_repr: str  # human string of the rule, e.g. "wave_height > 2.5 m"


class MarineDataResult(BaseModel):
    """Result of marine data specialist."""

    pfz_nodes: List[PFZNode]
    chlorophyll: Optional[Measurement] = None  # ISRO OCM, unit "mg_m3"
    sst: Optional[Measurement] = None  # sea-surface temp, unit "deg_c"
    source_freshness: dict = Field(default_factory=dict)  # source name -> datetime


class WeatherRiskResult(BaseModel):
    """Result of weather & risk specialist."""

    wave_height: Optional[Measurement] = None
    wind_speed: Optional[Measurement] = None
    cyclone_distance: Optional[Measurement] = None
    swell_surge: Optional[Measurement] = None
    safety_flags: List[SafetyFlag] = Field(default_factory=list)
    source_freshness: dict = Field(default_factory=dict)


class GeospatialResult(BaseModel):
    """Result of geospatial specialist."""

    nearest_pfz: Optional[PFZNode] = None
    distance_km: Optional[Measurement] = None
    bearing_deg: Optional[float] = None
    inside_imbl_buffer: Optional[bool] = None  # True if within warning buffer
    imbl_distance_km: Optional[Measurement] = None


class OceanAnalyticsResult(BaseModel):
    """Result of ocean analytics specialist (scaffold for v2)."""

    observation: Optional[str] = None  # stated as observation, never invented causation
    series: List[Measurement] = Field(default_factory=list)


class BoundingBox(BaseModel):
    """A geographic bounding box."""

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class ToolStatus(str, Enum):
    """Status of a tool response."""

    OK = "ok"
    EMPTY = "empty"  # query ran, no data for this area/time
    ERROR = "error"  # fetch failed (after adapter's own attempt)


class ToolResponse(BaseModel):
    """Response from any tool adapter."""

    status: ToolStatus
    retrieved_at: datetime
    source: SourceName
    payload: Optional[BaseModel] = None  # source-specific model
    error: Optional[str] = None  # error message if status=ERROR


class LLMMessage(BaseModel):
    """A message in LLM conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str
