"""SmartCP MCP Tools Package.

Provides the single "execute" tool that is the complete agent runtime.
"""

from smartcp.tools.execute import (
    get_runtime,
    register_execute_tool,
    set_runtime,
)

__all__ = [
    "register_execute_tool",
    "set_runtime",
    "get_runtime",
]
