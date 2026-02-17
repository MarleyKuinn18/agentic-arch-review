"""
Base types for local tools.
"""

from typing import Any, Callable

from pydantic import BaseModel


class ToolSpec(BaseModel):
    """Schema for a single tool: name, description, parameters."""

    name: str
    description: str
    parameters: dict[str, Any] = {}  # JSON Schema for args


class ToolResult(BaseModel):
    """Result of a tool invocation."""

    tool_name: str
    success: bool
    output: str | dict[str, Any]
    error: str | None = None


# Type for a callable that implements a tool: (args: dict) -> ToolResult
ToolImpl = Callable[[dict[str, Any]], ToolResult]
