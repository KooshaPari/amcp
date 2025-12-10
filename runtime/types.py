"""Runtime types for Agent Runtime execution."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Optional


class ExecutionStatus(str, Enum):
    """Execution status codes."""

    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of code execution in the agent runtime."""

    output: str
    """Standard output from execution."""
    error: Optional[str] = None
    """Standard error output, if any."""
    result: Optional[Any] = None
    """Return value from execution (if any)."""
    execution_time_ms: float = 0.0
    """Execution time in milliseconds."""
    variables: list[str] = field(default_factory=list)
    """List of variable names created/modified during execution."""
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    """Execution status."""


@dataclass
class SandboxResult:
    """Result from LangChain Sandbox execution."""

    stdout: str
    """Standard output."""
    stderr: str
    """Standard error."""
    return_value: Optional[Any] = None
    """Return value from execution."""
    execution_time_ms: float = 0.0
    """Execution time in milliseconds."""
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    """Execution status."""


@dataclass
class NamespaceConfig:
    """Configuration for building execution namespace."""

    include_tools: bool = True
    """Whether to include MCP tools in namespace."""
    include_scope: bool = True
    """Whether to include scope API."""
    include_mcp: bool = False
    """Whether to include MCP management API (Phase 3)."""
    include_skills: bool = False
    """Whether to include skills API (Phase 4)."""
    include_background: bool = False
    """Whether to include background task API (Phase 4)."""


@dataclass
class UserContext:
    """User context for runtime execution.

    Simplified wrapper around TokenPayload for runtime use.
    """

    user_id: str
    """User identifier."""
    workspace_id: Optional[str] = None
    """Workspace identifier."""
    permissions: list[str] = field(default_factory=list)
    """User permissions."""
    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""

    @classmethod
    def from_token_payload(cls, payload: Any) -> "UserContext":
        """Create UserContext from TokenPayload.

        Args:
            payload: TokenPayload from auth middleware

        Returns:
            UserContext instance
        """
        return cls(
            user_id=payload.user_id,
            workspace_id=payload.workspace_id,
            permissions=payload.permissions or [],
            metadata={
                "email": payload.email,
                "role": payload.role,
                "app_metadata": payload.app_metadata or {},
                "user_metadata": payload.user_metadata or {},
            },
        )


# Type aliases for clarity
ToolFunction = Callable[..., Coroutine[Any, Any, Any]]
ToolWrapper = Callable[[ToolFunction], ToolFunction]


# Type aliases for clarity
ToolFunction = Callable[..., Coroutine[Any, Any, Any]]
ToolWrapper = Callable[[ToolFunction], ToolFunction]
