"""Marine data discovery agent."""

from __future__ import annotations

from orca.agents.common import cell_id, force_error_for
from orca.guardrails.resilience import fetch
from orca.logging import get_logger
from orca.schemas import MarineDataResult, SourceName
from orca.state import PlatformState
from orca.tools.base import get_tool
from orca.tools.incois import PFZPayload, PFZRequest
from orca.tools.isro import ChlorophyllPayload, ChlorophyllRequest

logger = get_logger(__name__)


def marine_data_node(state: PlatformState) -> dict:
    """Fetch PFZ and ocean-colour data, retaining only typed tool facts."""
    freshness = dict(state.get("data_freshness") or {})
    cid = cell_id(state)
    pfz_response = fetch(
        get_tool("incois_get_pfz"),
        PFZRequest(
            cell_id=cid,
            force_error=force_error_for(state, SourceName.INCOIS_PFZ),
        ),
        SourceName.INCOIS_PFZ,
        freshness_dict=freshness,
    )
    isro_response = fetch(
        get_tool("isro_get_chlorophyll"),
        ChlorophyllRequest(
            cell_id=cid,
            force_error=force_error_for(state, SourceName.ISRO_CHLOROPHYLL),
        ),
        SourceName.ISRO_CHLOROPHYLL,
        freshness_dict=freshness,
    )
    payload = pfz_response.payload if isinstance(pfz_response.payload, PFZPayload) else None
    eo_payload = (
        isro_response.payload if isinstance(isro_response.payload, ChlorophyllPayload) else None
    )
    logger.info("marine_data fetched", extra={"extra_fields": {"pfz": pfz_response.status.value}})
    return {
        "data_freshness": freshness,
        "marine_data_result": MarineDataResult(
            pfz_nodes=list(payload.nodes) if payload else [],
            chlorophyll=eo_payload.chlorophyll if eo_payload else None,
            sst=eo_payload.sst if eo_payload else None,
            source_freshness={
                source: retrieved
                for source, retrieved in freshness.items()
                if source in (SourceName.INCOIS_PFZ, SourceName.ISRO_CHLOROPHYLL)
            },
        ),
    }
