"""SmartCP Execute Tool.

Single MCP tool that provides the complete agent runtime.
This is the ONLY entry point for code execution.
"""

import logging
from typing import Any

from smartcp.runtime import AgentRuntime, ExecutionResult, UserContext

logger = logging.getLogger(__name__)

# Global runtime instance (initialized by server)
_runtime: AgentRuntime | None = None


def set_runtime(runtime: AgentRuntime) -> None:
    """Set the global runtime instance.

    Called by server during startup.
    """
    global _runtime
    _runtime = runtime


def get_runtime() -> AgentRuntime:
    """Get the global runtime instance."""
    if _runtime is None:
        raise RuntimeError("Runtime not initialized. Call set_runtime() first.")
    return _runtime


def register_execute_tool(mcp: Any) -> None:
    """Register the execute tool with FastMCP server.

    Args:
        mcp: FastMCP server instance
    """
    from fastmcp import Context

    @mcp.tool()
    async def execute(
        code: str,
        timeout: int = 30,
        context: Context | None = None,
    ) -> dict[str, Any]:
        """Execute code in the agent runtime.

        This is the single MCP tool for SmartCP. The agent's code has access to:

        - All MCP tools as async callables: `await file_read(path)`
        - Scope API: `await scope.session.set("key", value)`
        - MCP management: `await mcp.search("database")`
        - Skills: `await skills.load("my-skill")`
        - Background tasks: `task = bg(expensive_op())`
        - Tool definition: `@tool def my_tool(): ...`

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (1-300)
            context: MCP context with user information

        Returns:
            Execution result with output, errors, and metadata

        Example:
            >>> # Simple execution
            >>> result = await execute("x = 1 + 1; print(x)")
            >>> print(result["output"])  # "2\n"

            >>> # Using scope API
            >>> await execute("await scope.session.set('count', 0)")
            >>> await execute("count = await scope.session.get('count'); print(count)")

            >>> # Using tools
            >>> await execute("files = await file_list('.'); print(files)")
        """
        runtime = get_runtime()

        # Extract user context from MCP context
        user_ctx = _extract_user_context(context)

        # Execute code
        result = await runtime.execute(
            code=code,
            user_ctx=user_ctx,
            timeout=timeout,
        )

        # Convert ExecutionResult to dict
        return {
            "output": result.output,
            "error": result.error,
            "result": result.result,
            "execution_time_ms": result.execution_time_ms,
            "variables": result.variables,
            "status": result.status.value,
        }

    @mcp.tool()
    async def clear_session(context: Context | None = None) -> dict[str, Any]:
        """Clear the current execution session.

        Removes all defined variables and resets state.
        """
        runtime = get_runtime()
        user_ctx = _extract_user_context(context)

        runtime.clear_session(user_ctx.user_id)

        return {
            "success": True,
            "message": "Session cleared",
        }

    @mcp.tool()
    async def runtime_status(context: Context | None = None) -> dict[str, Any]:
        """Get runtime status and diagnostics.

        Returns:
            Runtime status including active sessions and configuration
        """
        runtime = get_runtime()

        return {
            "initialized": runtime.sandbox._initialized,
            "active_sessions": len(runtime._session_cache),
        }

    logger.info("Registered execute tool with FastMCP")


def _extract_user_context(context: Any) -> UserContext:
    """Extract UserContext from MCP Context.

    The context contains user information from the auth middleware.
    """
    if context is None:
        # Anonymous user
        return UserContext(user_id="anonymous")

    # Try to get user info from context
    # The exact structure depends on how auth middleware stores it
    user_id = "anonymous"
    workspace_id = None

    # FastMCP context may have request state
    if hasattr(context, "request_context"):
        req_ctx = context.request_context
        if hasattr(req_ctx, "state"):
            state = req_ctx.state
            user_id = getattr(state, "user_id", None) or "anonymous"
            workspace_id = getattr(state, "workspace_id", None)

    return UserContext(
        user_id=user_id,
        workspace_id=workspace_id,
    )
