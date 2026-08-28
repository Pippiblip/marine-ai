"""Tool registry and base interfaces for mock-first data and channel adapters."""

from __future__ import annotations

from typing import ClassVar, Protocol

from pydantic import BaseModel

from orca.schemas import SourceName, ToolResponse


class ToolRequest(BaseModel):
    """Base request payload shared by all concrete tool requests."""


class Tool(Protocol):
    """Protocol for all tool adapters."""

    name: ClassVar[str]
    source: ClassVar[SourceName]

    def __call__(self, req: ToolRequest) -> ToolResponse:
        """Execute the tool and return a typed ToolResponse."""


def register(tool: Tool) -> Tool:
    """Register a tool in the global registry."""
    _REGISTRY[tool.name] = tool
    return tool


def get_tool(name: str) -> Tool:
    """Return a registered tool by name."""
    return _REGISTRY[name]


_REGISTRY: dict[str, Tool] = {}
