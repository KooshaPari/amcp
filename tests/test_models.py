"""Tests for models - enums, core, and schemas."""

import pytest

from models.enums import (
    MemoryScope,
    ExecutionLanguage,
    PatternType,
    ErrorCode,
)
from models.core import (
    UserContext,
    SmartCPError,
)
from models.schemas import (
    ExecuteCodeRequest,
    ExecuteCodeResponse,
)


# =============================================================================
# Enum Tests
# =============================================================================


class TestMemoryScope:
    """Tests for MemoryScope enum."""

    def test_values(self):
        """Test all memory scope values."""
        assert MemoryScope.USER.value == "user"
        assert MemoryScope.WORKSPACE.value == "workspace"
        assert MemoryScope.GLOBAL.value == "global"

    def test_string_comparison(self):
        """Test string comparison works."""
        assert MemoryScope.USER == "user"
        assert MemoryScope("user") == MemoryScope.USER


class TestExecutionLanguage:
    """Tests for ExecutionLanguage enum."""

    def test_values(self):
        """Test all language values."""
        assert ExecutionLanguage.PYTHON.value == "python"
        assert ExecutionLanguage.TYPESCRIPT.value == "typescript"
        assert ExecutionLanguage.BASH.value == "bash"
        assert ExecutionLanguage.GO.value == "go"
        assert ExecutionLanguage.RUST.value == "rust"
        assert ExecutionLanguage.JAVASCRIPT.value == "javascript"

    def test_from_string(self):
        """Test creating from string."""
        lang = ExecutionLanguage("python")
        assert lang == ExecutionLanguage.PYTHON


class TestPatternType:
    """Tests for PatternType enum."""

    def test_values(self):
        """Test all pattern type values."""
        assert PatternType.CODE_STYLE.value == "code_style"
        assert PatternType.ERROR_RESOLUTION.value == "error_resolution"
        assert PatternType.TOOL_USAGE.value == "tool_usage"
        assert PatternType.WORKFLOW.value == "workflow"
        assert PatternType.PREFERENCE.value == "preference"
        assert PatternType.CONTEXT.value == "context"
        assert PatternType.CUSTOM.value == "custom"


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_values(self):
        """Test all error code values."""
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorCode.NOT_FOUND.value == "NOT_FOUND"
        assert ErrorCode.PERMISSION_DENIED.value == "PERMISSION_DENIED"
        assert ErrorCode.RATE_LIMITED.value == "RATE_LIMITED"
        assert ErrorCode.EXECUTION_FAILED.value == "EXECUTION_FAILED"
        assert ErrorCode.EXECUTION_TIMEOUT.value == "EXECUTION_TIMEOUT"
        assert ErrorCode.MEMORY_LIMIT_EXCEEDED.value == "MEMORY_LIMIT_EXCEEDED"
        assert ErrorCode.STORAGE_ERROR.value == "STORAGE_ERROR"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"
        assert ErrorCode.AUTHENTICATION_REQUIRED.value == "AUTHENTICATION_REQUIRED"
        assert ErrorCode.INVALID_TOKEN.value == "INVALID_TOKEN"


# =============================================================================
# UserContext Tests
# =============================================================================


class TestUserContext:
    """Tests for UserContext dataclass."""

    def test_minimal_context(self):
        """Test creating context with just user_id."""
        ctx = UserContext(user_id="user-123")
        assert ctx.user_id == "user-123"
        assert ctx.device_id is None
        assert ctx.permissions == []
        assert ctx.context == {}

    def test_full_context(self):
        """Test creating context with all fields."""
        ctx = UserContext(
            user_id="user-123",
            device_id="device-456",
            session_id="session-789",
            project_id="project-abc",
            workspace_id="ws-def",
            cwd="/home/user",
            context={"key": "value"},
            permissions=["read", "write"],
            metadata={"source": "test"},
            request_id="req-123",
            trace_id="trace-456",
        )
        assert ctx.user_id == "user-123"
        assert ctx.device_id == "device-456"
        assert ctx.session_id == "session-789"
        assert ctx.project_id == "project-abc"
        assert ctx.workspace_id == "ws-def"
        assert ctx.cwd == "/home/user"
        assert ctx.context == {"key": "value"}
        assert ctx.permissions == ["read", "write"]
        assert ctx.metadata == {"source": "test"}
        assert ctx.request_id == "req-123"
        assert ctx.trace_id == "trace-456"

    def test_has_permission_explicit(self):
        """Test has_permission with explicit permission."""
        ctx = UserContext(user_id="user-123", permissions=["read", "write"])
        assert ctx.has_permission("read") is True
        assert ctx.has_permission("write") is True
        assert ctx.has_permission("delete") is False

    def test_has_permission_wildcard(self):
        """Test has_permission with wildcard."""
        ctx = UserContext(user_id="user-123", permissions=["*"])
        assert ctx.has_permission("read") is True
        assert ctx.has_permission("write") is True
        assert ctx.has_permission("anything") is True

    def test_has_permission_empty(self):
        """Test has_permission with no permissions."""
        ctx = UserContext(user_id="user-123")
        assert ctx.has_permission("read") is False

    def test_to_dict(self):
        """Test converting to dictionary."""
        ctx = UserContext(
            user_id="user-123",
            device_id="device-456",
            permissions=["read"],
        )
        d = ctx.to_dict()
        assert d["user_id"] == "user-123"
        assert d["device_id"] == "device-456"
        assert d["permissions"] == ["read"]
        assert "context" in d
        assert "metadata" in d

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "user_id": "user-123",
            "device_id": "device-456",
            "permissions": ["admin"],
            "context": {"env": "test"},
        }
        ctx = UserContext.from_dict(data)
        assert ctx.user_id == "user-123"
        assert ctx.device_id == "device-456"
        assert ctx.permissions == ["admin"]
        assert ctx.context == {"env": "test"}

    def test_from_dict_minimal(self):
        """Test from_dict with minimal data."""
        data = {"user_id": "user-123"}
        ctx = UserContext.from_dict(data)
        assert ctx.user_id == "user-123"
        assert ctx.device_id is None
        assert ctx.permissions == []

    def test_roundtrip(self):
        """Test to_dict -> from_dict roundtrip."""
        original = UserContext(
            user_id="user-123",
            workspace_id="ws-456",
            permissions=["read", "write"],
            metadata={"key": "value"},
        )
        data = original.to_dict()
        restored = UserContext.from_dict(data)

        assert restored.user_id == original.user_id
        assert restored.workspace_id == original.workspace_id
        assert restored.permissions == original.permissions
        assert restored.metadata == original.metadata


# =============================================================================
# SmartCPError Tests
# =============================================================================


class TestSmartCPError:
    """Tests for SmartCPError model."""

    def test_minimal_error(self):
        """Test creating error with required fields."""
        error = SmartCPError(
            error="Something went wrong",
            error_code=ErrorCode.INTERNAL_ERROR,
        )
        assert error.success is False
        assert error.error == "Something went wrong"
        assert error.error_code == ErrorCode.INTERNAL_ERROR
        assert error.details is None
        assert error.request_id is None

    def test_full_error(self):
        """Test creating error with all fields."""
        error = SmartCPError(
            error="Validation failed",
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"field": "email", "reason": "invalid format"},
            request_id="req-123",
        )
        assert error.error == "Validation failed"
        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.details["field"] == "email"
        assert error.request_id == "req-123"

    def test_success_always_false(self):
        """Test that success is always False."""
        error = SmartCPError(
            error="Error",
            error_code=ErrorCode.INTERNAL_ERROR,
        )
        assert error.success is False

    def test_to_dict(self):
        """Test to_dict method."""
        error = SmartCPError(
            error="Not found",
            error_code=ErrorCode.NOT_FOUND,
            details={"id": "123"},
        )
        d = error.to_dict()
        assert d["success"] is False
        assert d["error"] == "Not found"
        assert d["error_code"] == "NOT_FOUND"
        assert d["details"]["id"] == "123"

    def test_to_dict_excludes_none(self):
        """Test to_dict excludes None values."""
        error = SmartCPError(
            error="Error",
            error_code=ErrorCode.INTERNAL_ERROR,
        )
        d = error.to_dict()
        assert "details" not in d
        assert "request_id" not in d


# =============================================================================
# ExecuteCodeRequest Tests
# =============================================================================


class TestExecuteCodeRequest:
    """Tests for ExecuteCodeRequest model."""

    def test_minimal_request(self):
        """Test creating request with just code."""
        request = ExecuteCodeRequest(code="print('hello')")
        assert request.code == "print('hello')"
        assert request.language == ExecutionLanguage.PYTHON
        assert request.timeout == 30
        assert request.context == {}

    def test_full_request(self):
        """Test creating request with all fields."""
        request = ExecuteCodeRequest(
            code="console.log('hello')",
            language=ExecutionLanguage.TYPESCRIPT,
            timeout=60,
            context={"env": "test"},
        )
        assert request.code == "console.log('hello')"
        assert request.language == ExecutionLanguage.TYPESCRIPT
        assert request.timeout == 60
        assert request.context == {"env": "test"}

    def test_timeout_bounds(self):
        """Test timeout validation."""
        # Valid timeout
        request = ExecuteCodeRequest(code="x", timeout=100)
        assert request.timeout == 100

        # Below minimum
        with pytest.raises(ValueError):
            ExecuteCodeRequest(code="x", timeout=0)

        # Above maximum
        with pytest.raises(ValueError):
            ExecuteCodeRequest(code="x", timeout=500)


# =============================================================================
# ExecuteCodeResponse Tests
# =============================================================================


class TestExecuteCodeResponse:
    """Tests for ExecuteCodeResponse model."""

    def test_success_response(self):
        """Test successful execution response."""
        response = ExecuteCodeResponse(
            execution_id="exec-123",
            status="completed",
            output="Hello, World!\n",
            result=42,
            variables=["x", "y"],
            execution_time_ms=15.5,
        )
        assert response.execution_id == "exec-123"
        assert response.status == "completed"
        assert response.output == "Hello, World!\n"
        assert response.error is None
        assert response.result == 42
        assert response.variables == ["x", "y"]
        assert response.execution_time_ms == 15.5

    def test_error_response(self):
        """Test error execution response."""
        response = ExecuteCodeResponse(
            execution_id="exec-456",
            status="failed",
            error="NameError: name 'undefined' is not defined",
        )
        assert response.status == "failed"
        assert response.error is not None
        assert response.output is None
        assert response.result is None

    def test_timeout_response(self):
        """Test timeout execution response."""
        response = ExecuteCodeResponse(
            execution_id="exec-789",
            status="timeout",
            error="Execution exceeded 30 second limit",
        )
        assert response.status == "timeout"
        assert "30 second" in response.error

    def test_default_values(self):
        """Test default values for optional fields."""
        response = ExecuteCodeResponse(
            execution_id="exec-000",
            status="completed",
        )
        assert response.output is None
        assert response.error is None
        assert response.result is None
        assert response.variables == []
        assert response.execution_time_ms is None
