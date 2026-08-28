"""Scaffold for future historical ocean analytics."""

from orca.state import PlatformState


def ocean_analytics_node(state: PlatformState) -> dict:
    """Return no analytics until the Copernicus adapter is implemented."""
    # TODO(orca): add historical Copernicus series and observation analysis.
    return {"ocean_analytics_result": None}
