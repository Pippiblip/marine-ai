"""Scaffold for the future always-on alert service."""

from orca.state import PlatformState


def alert_notification_node(state: PlatformState) -> dict:
    """Keep alert delivery out of the request/response graph for now."""
    # TODO(orca): watch cyclone and swell polygons and notify subscribed users.
    return {}
