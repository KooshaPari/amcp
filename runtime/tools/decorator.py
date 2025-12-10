"""Tool decorator for defining tools in agent code."""

import logging
from typing import Any, Callable

from smartcp.runtime.tools.registry import ToolRegistry
from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


def create_tool_decorator(
    tool_registry: ToolRegistry,
    user_ctx: UserContext,
) -> Callable:
    """Create @tool decorator for namespace injection.

    Args:
        tool_registry: Tool registry to register tools with
        user_ctx: User context for scoped tools

    Returns:
        Tool decorator function
    """
    def tool(
        name: str | None = None,
        description: str | None = None,
    ) -> Callable:
        """Decorator to register a function as a tool.

        Usage:
            @tool
            def my_tool(param: str) -> dict:
                '''Tool description.'''
                return {"result": param}

            @tool(name="custom_name", description="Custom description")
            def another_tool() -> dict:
                return {"status": "ok"}
        """

        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""

            tool_registry.register(
                name=tool_name,
                description=tool_desc,
                func=func,
                user_ctx=user_ctx,
            )

            logger.info(f"Registered tool via decorator: {tool_name}")
            return func

        return decorator

    return tool
