"""Optional MCP server exposure of registry tools — scaffold."""

# TODO(orca): wrap get_tool() registry as MCP endpoints so external agents
# can list tools and call incois_get_pfz against fixtures.

def list_mcp_tools() -> list[str]:
    """Return tool names that would be exposed over MCP."""
    from orca.tools.base import get_tool

    names = [
        "incois_get_pfz",
        "incois_get_ocean_state",
        "imd_get_marine_warnings",
        "isro_get_chlorophyll",
    ]
    return [name for name in names if get_tool(name)]
