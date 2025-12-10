"""Unit tests for runtime types."""

import pytest

from smartcp.runtime.types import (
    ExecutionResult,
    ExecutionStatus,
    NamespaceConfig,
    SandboxResult,
    UserContext,
)


class TestExecutionStatus:
    """Test ExecutionStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert ExecutionStatus.COMPLETED == "completed"
        assert ExecutionStatus.FAILED == "failed"
        assert ExecutionStatus.TIMEOUT == "timeout"
        assert ExecutionStatus.CANCELLED == "cancelled"


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_create_result(self):
        """Test creating an execution result."""
        result = ExecutionResult(
            output="test output",
            error=None,
            result=42,
            execution_time_ms=100.0,
            variables=["x", "y"],
            status=ExecutionStatus.COMPLETED,
        )

        assert result.output == "test output"
        assert result.error is None
        assert result.result == 42
        assert result.execution_time_ms == 100.0
        assert result.variables == ["x", "y"]
        assert result.status == ExecutionStatus.COMPLETED

    def test_result_with_error(self):
        """Test result with error."""
        result = ExecutionResult(
            output="",
            error="Something went wrong",
            status=ExecutionStatus.FAILED,
        )

        assert result.error == "Something went wrong"
        assert result.status == ExecutionStatus.FAILED


class TestSandboxResult:
    """Test SandboxResult dataclass."""

    def test_create_sandbox_result(self):
        """Test creating a sandbox result."""
        result = SandboxResult(
            stdout="output",
            stderr="",
            return_value=42,
            execution_time_ms=50.0,
            status=ExecutionStatus.COMPLETED,
        )

        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.return_value == 42
        assert result.execution_time_ms == 50.0
        assert result.status == ExecutionStatus.COMPLETED


class TestNamespaceConfig:
    """Test NamespaceConfig dataclass."""

    def test_default_config(self):
        """Test default namespace config."""
        config = NamespaceConfig()

        assert config.include_tools is True
        assert config.include_scope is True
        assert config.include_mcp is False
        assert config.include_skills is False
        assert config.include_background is False

    def test_custom_config(self):
        """Test custom namespace config."""
        config = NamespaceConfig(
            include_tools=False,
            include_scope=False,
            include_mcp=True,
        )

        assert config.include_tools is False
        assert config.include_scope is False
        assert config.include_mcp is True


class TestUserContext:
    """Test UserContext dataclass."""

    def test_create_user_context(self):
        """Test creating a user context."""
        ctx = UserContext(
            user_id="user-123",
            workspace_id="ws-456",
            permissions=["read", "write"],
            metadata={"key": "value"},
        )

        assert ctx.user_id == "user-123"
        assert ctx.workspace_id == "ws-456"
        assert ctx.permissions == ["read", "write"]
        assert ctx.metadata == {"key": "value"}

    def test_user_context_defaults(self):
        """Test user context with defaults."""
        ctx = UserContext(user_id="user-123")

        assert ctx.user_id == "user-123"
        assert ctx.workspace_id is None
        assert ctx.permissions == []
        assert ctx.metadata == {}

    def test_from_token_payload(self):
        """Test creating UserContext from token payload."""
        class MockPayload:
            def __init__(self):
                self.user_id = "user-123"
                self.workspace_id = "ws-456"
                self.permissions = ["read"]
                self.email = "test@example.com"
                self.role = "user"
                self.app_metadata = {"key": "app"}
                self.user_metadata = {"key": "user"}

        payload = MockPayload()
        ctx = UserContext.from_token_payload(payload)

        assert ctx.user_id == "user-123"
        assert ctx.workspace_id == "ws-456"
        assert ctx.permissions == ["read"]
        assert ctx.metadata["email"] == "test@example.com"
        assert ctx.metadata["role"] == "user"
