"""Tool definition types."""

from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from smartcp.runtime.types import UserContext

ToolFunction = Callable[..., Coroutine[Any, Any, Any]]


@dataclass
class ToolDefinition:
    """Definition of a tool available in the runtime."""

    name: str
    """Tool name."""
    description: str
    """Tool description."""
    func: ToolFunction
    """Async function implementing the tool."""
    user_ctx: UserContext | None = None
    """User context if tool is user-scoped."""
