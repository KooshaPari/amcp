"""Agent Runtime package.

Provides sandboxed code execution with tool injection and scope management.
"""

from smartcp.runtime.core import AgentRuntime
from smartcp.runtime.sandbox import SandboxWrapper
from smartcp.runtime.types import (
    ExecutionResult,
    ExecutionStatus,
    NamespaceConfig,
    UserContext,
)

__all__ = [
    "AgentRuntime",
    "SandboxWrapper",
    "ExecutionResult",
    "ExecutionStatus",
    "NamespaceConfig",
    "UserContext",
]
