"""User-Scoped Code Executor Service for SmartCP.

Provides sandboxed code execution scoped to users via UserContext.
All execution state and variables are isolated per user.

This module has been decomposed into focused submodules:
- core.py: Main executor orchestration
- subprocess.py: Subprocess and code execution management
- results.py: Execution result handling and serialization
- sandboxing.py: Security checking and safe builtins configuration
"""

from typing import Any, Optional

from smartcp.services.memory import UserScopedMemory
from smartcp.services.models import ExecuteCodeRequest, ExecuteCodeResponse

from .core import UserScopedExecutor
from .results import ExecutionResult
from .sandboxing import SecurityChecker

__all__ = [
    # Main executor
    "UserScopedExecutor",
    # Request/Response models (from services.models, re-exported for convenience)
    "ExecuteCodeRequest",
    "ExecuteCodeResponse",
    # Error classes (from old executor.py, preserved for compatibility)
    "ExecutionError",
    "SecurityError",
    # Result and configuration
    "ExecutionResult",
    "SecurityChecker",
    # Factory function
    "create_executor_service",
]


class ExecutionError(Exception):
    """Error during code execution."""

    def __init__(self, message: str, code: str = "EXECUTION_ERROR", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class SecurityError(ExecutionError):
    """Security violation during code execution."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "SECURITY_ERROR", details)


def create_executor_service(
    memory: Optional[UserScopedMemory] = None,
    bifrost_client: Any = None,
    allow_local_fallback: bool = False,
) -> UserScopedExecutor:
    """Factory function to create an executor service.

    Args:
        memory: Memory service (created if not provided)
        bifrost_client: Optional Bifrost client for delegated execution

    Returns:
        Configured UserScopedExecutor instance
    """
    if memory is None:
        from smartcp.services.memory import create_memory_service
        memory = create_memory_service()

    if bifrost_client is None:
        from smartcp.infrastructure.bifrost.client import BifrostClient
        bifrost_client = BifrostClient()

    executor = UserScopedExecutor(
        memory,
        security_checker=None,
        bifrost_client=bifrost_client,
        allow_local_fallback=allow_local_fallback,
    )
    return executor
