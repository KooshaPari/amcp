"""Execute Code MCP Tool for SmartCP.

Provides the execute_code MCP tool that enables sandboxed
Python code execution with user-scoped variable persistence.
"""

import logging
from typing import Any, Optional

from auth.context import get_request_context
from services.executor import UserScopedExecutor
from services.models import ExecuteCodeRequest, ExecuteCodeResponse, ExecutionLanguage, ExecutionStatus

logger = logging.getLogger(__name__)


def register_execute_tool(mcp: Any, executor: UserScopedExecutor) -> None:
    """Register the execute_code tool with the MCP server.

    Args:
        mcp: FastMCP server instance
        executor: UserScopedExecutor service
    """

    @mcp.tool()
    async def execute_code(
        code: str,
        language: str = "python",
        timeout: int = 30,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Execute code in a sandboxed environment.

        This tool executes Python code in a secure sandbox with:
        - User-isolated variable namespace (variables persist across calls)
        - Security checks to prevent dangerous operations
        - Timeout enforcement
        - Output capture

        Args:
            code: The code to execute
            language: Programming language (currently only "python" supported)
            timeout: Maximum execution time in seconds (1-300, default 30)
            context: Optional context variables to inject

        Returns:
            Dictionary with execution results:
            - execution_id: Unique identifier for this execution
            - status: "completed", "failed", or "timeout"
            - output: Standard output from the code
            - error: Error message if execution failed
            - result: Return value of the last expression
            - variables: List of variables created/updated

        Examples:
            # Simple calculation
            execute_code(code="x = 2 + 2")
            # Result: {"status": "completed", "variables": ["x"]}

            # Access previous variable
            execute_code(code="print(x * 10)")
            # Result: {"status": "completed", "output": "40\\n"}

            # Define a function
            execute_code(code=\"\"\"
            def greet(name):
                return f"Hello, {name}!"
            result = greet("World")
            \"\"\")
            # Result: {"status": "completed", "result": "Hello, World!"}
        """
        # Get user context from request
        user_ctx = get_request_context()
        if user_ctx is None:
            logger.error("No user context available for execute_code")
            return {
                "execution_id": "",
                "status": "failed",
                "error": "Authentication required",
                "output": None,
                "result": None,
                "variables": [],
            }

        logger.info(
            "execute_code tool called",
            extra={
                "user_id": user_ctx.user_id,
                "language": language,
                "code_length": len(code),
                "request_id": user_ctx.request_id,
            },
        )

        # Validate language
        try:
            exec_language = ExecutionLanguage(language.lower())
        except ValueError:
            return {
                "execution_id": "",
                "status": "failed",
                "error": f"Unsupported language: {language}. Only 'python' is supported.",
                "output": None,
                "result": None,
                "variables": [],
            }

        # Build request
        request = ExecuteCodeRequest(
            code=code,
            language=exec_language,
            timeout=min(max(timeout, 1), 300),  # Clamp to 1-300
            context=context or {},
        )

        # Execute
        response = await executor.execute(user_ctx, request)

        return {
            "execution_id": response.execution_id,
            "status": response.status.value,
            "output": response.output,
            "error": response.error,
            "result": response.result,
            "variables": response.variables or [],
            "execution_time_ms": response.execution_time_ms,
        }

    @mcp.tool()
    async def get_variables() -> dict[str, Any]:
        """Get all variables in the current execution namespace.

        Returns a dictionary of all user-defined variables that have been
        created through previous execute_code calls.

        Returns:
            Dictionary with:
            - variables: Dictionary of variable name -> value
            - count: Number of variables

        Example:
            # After running execute_code(code="x = 1; y = 2")
            get_variables()
            # Result: {"variables": {"x": 1, "y": 2}, "count": 2}
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"variables": {}, "count": 0, "error": "Authentication required"}

        variables = await executor.get_variables(user_ctx)
        return {
            "variables": variables,
            "count": len(variables),
        }

    @mcp.tool()
    async def set_variable(
        name: str,
        value: Any,
    ) -> dict[str, Any]:
        """Set a variable in the execution namespace.

        Directly sets a variable without executing code. The variable
        will be available in subsequent execute_code calls.

        Args:
            name: Variable name (must be a valid Python identifier)
            value: Variable value (must be JSON-serializable)

        Returns:
            Dictionary with:
            - success: Whether the operation succeeded
            - name: The variable name
            - error: Error message if failed

        Example:
            set_variable(name="config", value={"debug": True})
            execute_code(code="print(config)")
            # Output: {"debug": True}
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "error": "Authentication required"}

        try:
            await executor.set_variable(user_ctx, name, value)
            return {"success": True, "name": name}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(
                "Failed to set variable",
                extra={
                    "user_id": user_ctx.user_id,
                    "variable": name,
                    "error": str(e),
                },
            )
            return {"success": False, "error": f"Failed to set variable: {e}"}

    @mcp.tool()
    async def delete_variable(name: str) -> dict[str, Any]:
        """Delete a variable from the execution namespace.

        Args:
            name: Variable name to delete

        Returns:
            Dictionary with:
            - success: Whether the variable was deleted
            - name: The variable name

        Example:
            delete_variable(name="temp_data")
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "error": "Authentication required"}

        deleted = await executor.delete_variable(user_ctx, name)
        return {"success": deleted, "name": name}

    @mcp.tool()
    async def clear_variables() -> dict[str, Any]:
        """Clear all variables from the execution namespace.

        Removes all user-defined variables. Use with caution.

        Returns:
            Dictionary with:
            - success: Whether the operation succeeded
            - count: Number of variables cleared

        Example:
            clear_variables()
            # Result: {"success": True, "count": 5}
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "count": 0, "error": "Authentication required"}

        count = await executor.clear_variables(user_ctx)
        return {"success": True, "count": count}

    logger.info("Registered execute_code tools with MCP server")
