"""Data models for executor service."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class ExecutionLanguage(str, Enum):
    """Supported execution languages."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    GO = "go"


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    COMPLETED = "completed"  # Alias for SUCCESS
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class UserContext:
    """User context for request isolation."""
    user_id: str
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    cwd: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    trace_id: Optional[str] = None

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid4())


@dataclass
class ExecuteCodeRequest:
    """Request to execute code."""
    code: str
    language: ExecutionLanguage = ExecutionLanguage.PYTHON
    timeout: Optional[int] = None
    context: Optional[dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timeout is None:
            self.timeout = 30
        if self.context is None:
            self.context = {}


@dataclass
class ExecuteCodeResponse:
    """Response from code execution."""
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    status: ExecutionStatus = ExecutionStatus.PENDING
    output: str = ""
    error: Optional[str] = None
    result: Any = None
    variables: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
