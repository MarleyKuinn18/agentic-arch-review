"""
Tool registry and invocation for local tool calling.
"""

from typing import Any

from arch_review_agent.tools.base import ToolResult, ToolSpec, ToolImpl


class ToolRegistry:
    """
    Registry of available tools. Register specs and implementations, then invoke by name.
    """

    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._impls: dict[str, ToolImpl] = {}

    def register(self, spec: ToolSpec, impl: ToolImpl) -> None:
        """Register a tool by spec and implementation."""
        self._specs[spec.name] = spec
        self._impls[spec.name] = impl

    def list_tools(self) -> list[ToolSpec]:
        """Return all registered tool specs (for LLM tool choice)."""
        return list(self._specs.values())

    def get_spec(self, name: str) -> ToolSpec | None:
        return self._specs.get(name)

    def invoke(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Invoke a tool by name with given arguments."""
        impl = self._impls.get(name)
        if not impl:
            return ToolResult(tool_name=name, success=False, output={}, error=f"Unknown tool: {name}")
        try:
            return impl(arguments)
        except Exception as e:
            return ToolResult(tool_name=name, success=False, output={}, error=str(e))


# Default registry instance; modules can register tools on import
_default_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    return _default_registry


def invoke_tool(name: str, arguments: dict[str, Any], registry: ToolRegistry | None = None) -> ToolResult:
    """Convenience: invoke a tool from the default or given registry."""
    reg = registry or _default_registry
    return reg.invoke(name, arguments)


# TODO: Define and register concrete tools (e.g. extract_sections, word_count, validate_headers)
# in a tools/ or tools/plugins module and register them with get_registry().
