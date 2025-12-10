"""Agent Runtime core - orchestrates code execution.

The AgentRuntime is the central component that coordinates sandbox execution,
namespace building, and session management.
"""

import logging
from typing import Any, Optional

from smartcp.runtime.namespace import NamespaceBuilder
from smartcp.runtime.sandbox import SandboxWrapper
from smartcp.runtime.types import (
    ExecutionResult,
    ExecutionStatus,
    NamespaceConfig,
    UserContext,
)

logger = logging.getLogger(__name__)


class AgentRuntime:
    """Complete agent runtime environment.

    Coordinates code execution in a sandboxed environment with:
    - Variable persistence across executions
    - Tool injection into namespace
    - Scope management
    - MCP tool integration
    """

    def __init__(self, tool_registry: "ToolRegistry | None" = None):
        """Initialize agent runtime.

        Args:
            tool_registry: Optional tool registry (creates new if not provided)
        """
        from smartcp.runtime.tools.registry import ToolRegistry

        self.sandbox = SandboxWrapper()
        self.tool_registry = tool_registry or ToolRegistry()
        self._session_cache: dict[str, bytes] = {}
        logger.info("AgentRuntime initialized")

    async def execute(
        self,
        code: str,
        user_ctx: UserContext,
        timeout: int = 30,
        namespace_config: Optional[NamespaceConfig] = None,
    ) -> ExecutionResult:
        """Execute code in agent runtime.

        Args:
            code: Python code to execute
            user_ctx: User context for scoped operations
            timeout: Execution timeout in seconds
            namespace_config: Optional namespace configuration

        Returns:
            ExecutionResult with output, error, result, and timing
        """
        if namespace_config is None:
            namespace_config = NamespaceConfig()

        # 1. Build namespace with all tools and APIs
        namespace_builder = NamespaceBuilder(namespace_config, user_ctx, self.tool_registry)
        namespace = await namespace_builder.build()

        # 2. Load user's session (for variable persistence)
        session = self._session_cache.get(user_ctx.user_id)

        # 3. Ensure sandbox is initialized
        if not self.sandbox._initialized:
            await self.sandbox.initialize()

        # 4. Load session if available
        if session:
            self.sandbox.load_session(session)

        # 5. Execute in sandbox
        sandbox_result = await self.sandbox.execute(
            code=code,
            namespace=namespace,
            session=session,
            timeout=timeout,
        )

        # 6. Save new session state
        new_session = self.sandbox.get_session()
        if new_session:
            self._session_cache[user_ctx.user_id] = new_session

        # 7. Convert to ExecutionResult
        return ExecutionResult(
            output=sandbox_result.stdout,
            error=sandbox_result.stderr if sandbox_result.stderr else None,
            result=sandbox_result.return_value,
            execution_time_ms=sandbox_result.execution_time_ms,
            variables=[],  # Phase 2: Extract from session
            status=sandbox_result.status,
        )

    def clear_session(self, user_id: str) -> None:
        """Clear session for a user.

        Args:
            user_id: User identifier
        """
        if user_id in self._session_cache:
            del self._session_cache[user_id]
            logger.info("Session cleared", extra={"user_id": user_id})

    def get_session(self, user_id: str) -> Optional[bytes]:
        """Get session bytes for a user.

        Args:
            user_id: User identifier

        Returns:
            Session bytes or None if no session exists
        """
        return self._session_cache.get(user_id)
