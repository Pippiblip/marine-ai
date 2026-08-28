"""Intent routing for the ORCA graph."""

from orca.llm.factory import get_llm
from orca.logging import get_logger
from orca.state import PlatformState

logger = get_logger(__name__)

_INTENTS = ["pfz_nearest", "safety_check", "boundary_check", "conditions_summary"]
_SUBTASKS = {
    "pfz_nearest": ["marine_data", "geospatial", "weather_risk"],
    "safety_check": ["weather_risk", "geospatial"],
    "boundary_check": ["geospatial"],
    "conditions_summary": ["weather_risk"],
}


def router_node(state: PlatformState) -> dict:
    """Classify the query against a fixed intent set and plan its specialists."""
    intent = get_llm().classify(state.get("query_text", ""), _INTENTS)
    subtasks = list(_SUBTASKS[intent])
    logger.info("router classified", extra={"extra_fields": {"intent": intent, "subtasks": subtasks}})
    return {"intent": intent, "subtasks": subtasks}
