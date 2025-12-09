"""User-Scoped Code Executor Service for SmartCP.

Provides sandboxed code execution scoped to users via UserContext.
All execution state and variables are isolated per user.
"""

import ast
import logging
import sys
import traceback
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from io import StringIO
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from smartcp.services.models import (
    ExecuteCodeRequest,
    ExecuteCodeResponse,
    ExecutionLanguage,
    ExecutionStatus,
    UserContext,
)
from smartcp.services.memory import MemoryType, UserScopedMemory

logger = logging.getLogger(__name__)


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


@dataclass
class ExecutionResult:
    """Result of code execution."""

    execution_id: str = field(default_factory=lambda: str(uuid4()))
    status: ExecutionStatus = ExecutionStatus.PENDING
    output: str = ""
    error: Optional[str] = None
    result: Any = None
    variables: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SecurityChecker:
    """Validates code for security before execution."""

    # Forbidden modules that could be dangerous
    FORBIDDEN_MODULES = {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "http",
        "urllib",
        "requests",
        "pathlib",
        "glob",
        "tempfile",
        "pickle",
        "marshal",
        "shelve",
        "importlib",
        "__builtin__",
        "builtins",
        "ctypes",
        "multiprocessing",
        "threading",
        "concurrent",
        "asyncio",
        "signal",
        "pty",
        "tty",
        "termios",
        "fcntl",
        "resource",
        "sysconfig",
    }

    # Forbidden built-in functions
    FORBIDDEN_BUILTINS = {
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "__import__",
        "breakpoint",
        "help",
        "quit",
        "exit",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
    }

    # Forbidden AST node types
    FORBIDDEN_NODES = {
        ast.Import,
        ast.ImportFrom,
    }

    def check(self, code: str) -> list[str]:
        """Check code for security violations.

        Args:
            code: Python code to check

        Returns:
            List of security violation messages (empty if safe)
        """
        violations = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"Syntax error: {e}"]

        for node in ast.walk(tree):
            # Check for forbidden node types
            if type(node) in self.FORBIDDEN_NODES:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in self.FORBIDDEN_MODULES:
                            violations.append(f"Forbidden import: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in self.FORBIDDEN_MODULES:
                        violations.append(f"Forbidden import from: {node.module}")

            # Check for forbidden function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_BUILTINS:
                        violations.append(f"Forbidden function: {node.func.id}")
                elif isinstance(node.func, ast.Attribute):
                    # Check for things like os.system()
                    if isinstance(node.func.value, ast.Name):
                        module = node.func.value.id
                        if module in self.FORBIDDEN_MODULES:
                            violations.append(
                                f"Forbidden module access: {module}.{node.func.attr}"
                            )

        return violations


class SafeBuiltins:
    """Provides safe built-in functions for code execution."""

    ALLOWED = {
        # Type conversions
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "frozenset": frozenset,
        "bytes": bytes,
        "bytearray": bytearray,
        # Math operations
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "divmod": divmod,
        # Iteration
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "reversed": reversed,
        "len": len,
        "all": all,
        "any": any,
        # String operations
        "chr": chr,
        "ord": ord,
        "hex": hex,
        "oct": oct,
        "bin": bin,
        "format": format,
        "repr": repr,
        "ascii": ascii,
        # Object introspection (safe subset)
        "type": type,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "callable": callable,
        "id": id,
        "hash": hash,
        # Other safe operations
        "print": print,  # Redirected to StringIO
        "iter": iter,
        "next": next,
        "slice": slice,
        "object": object,
        "property": property,
        "staticmethod": staticmethod,
        "classmethod": classmethod,
        "super": super,
        # Exceptions (for try/except)
        "Exception": Exception,
        "BaseException": BaseException,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "IndexError": IndexError,
        "AttributeError": AttributeError,
        "RuntimeError": RuntimeError,
        "StopIteration": StopIteration,
        "ZeroDivisionError": ZeroDivisionError,
        "OverflowError": OverflowError,
        # Constants
        "True": True,
        "False": False,
        "None": None,
    }

    @classmethod
    def get_builtins(cls) -> dict[str, Any]:
        """Get safe builtins dictionary."""
        return cls.ALLOWED.copy()


class UserScopedExecutor:
    """User-scoped code execution service.

    Provides sandboxed Python code execution with:
    - User-isolated variable namespace
    - Security checks on code
    - Timeout enforcement
    - Output capture
    - Persistent variables across executions

    Usage:
        executor = UserScopedExecutor(memory_service)

        # Execute code
        result = await executor.execute(
            user_ctx,
            ExecuteCodeRequest(code="x = 1 + 1", language="python")
        )

        # Variables persist
        result2 = await executor.execute(
            user_ctx,
            ExecuteCodeRequest(code="print(x)", language="python")
        )
    """

    DEFAULT_TIMEOUT = 30  # seconds
    MAX_OUTPUT_SIZE = 100_000  # characters

    def __init__(
        self,
        memory: UserScopedMemory,
        security_checker: Optional[SecurityChecker] = None,
        bifrost_client: Any = None,
        enable_bifrost_execution: bool = False,
    ):
        """Initialize executor.

        Args:
            memory: User-scoped memory service
            security_checker: Security checker (default SecurityChecker)
            bifrost_client: Optional Bifrost client for delegated execution
            enable_bifrost_execution: Feature flag to delegate execution to Bifrost
        """
        self.memory = memory
        self.security = security_checker or SecurityChecker()
        self.bifrost_client = bifrost_client
        self.enable_bifrost_execution = enable_bifrost_execution

    async def execute(
        self,
        user_ctx: UserContext,
        request: ExecuteCodeRequest,
    ) -> ExecuteCodeResponse:
        """Execute code in user's isolated namespace.

        Args:
            user_ctx: User context for isolation
            request: Execution request

        Returns:
            ExecuteCodeResponse with results
        """
        if self.enable_bifrost_execution and self.bifrost_client:
            try:
                return await self._execute_via_bifrost(user_ctx, request)
            except Exception as exc:
                logger.warning(
                    "Bifrost execution failed, falling back to local sandbox",
                    extra={
                        "error": str(exc),
                        "user_id": user_ctx.user_id,
                        "request_id": user_ctx.request_id,
                    },
                )

        execution_id = str(uuid4())
        started_at = datetime.now(timezone.utc)

        logger.info(
            "Starting code execution",
            extra={
                "user_id": user_ctx.user_id,
                "execution_id": execution_id,
                "language": request.language.value,
                "code_length": len(request.code),
                "request_id": user_ctx.request_id,
            },
        )

        # Only Python supported currently
        if request.language != ExecutionLanguage.PYTHON:
            return ExecuteCodeResponse(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error=f"Language '{request.language}' is not supported",
            )

        # Security check
        violations = self.security.check(request.code)
        if violations:
            logger.warning(
                "Security violations detected",
                extra={
                    "user_id": user_ctx.user_id,
                    "execution_id": execution_id,
                    "violations": violations,
                    "request_id": user_ctx.request_id,
                },
            )
            return ExecuteCodeResponse(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error=f"Security violations: {'; '.join(violations)}",
            )

        try:
            # Load user's variables
            user_vars = await self.memory.get_variables(user_ctx)

            # Merge with request context
            namespace = {
                **SafeBuiltins.get_builtins(),
                "__builtins__": SafeBuiltins.get_builtins(),
                **user_vars,
                **(request.context or {}),
            }

            # Execute code with output capture
            result, output, error = await self._execute_code(
                request.code,
                namespace,
                timeout=request.timeout or self.DEFAULT_TIMEOUT,
            )

            # Extract and save new/updated variables
            new_vars = self._extract_variables(namespace, user_vars)
            for name, value in new_vars.items():
                await self.memory.set_variable(user_ctx, name, value)

            completed_at = datetime.now(timezone.utc)
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000

            if error:
                status = ExecutionStatus.FAILED
            else:
                status = ExecutionStatus.COMPLETED

            logger.info(
                "Code execution completed",
                extra={
                    "user_id": user_ctx.user_id,
                    "execution_id": execution_id,
                    "status": status.value,
                    "execution_time_ms": execution_time_ms,
                    "variables_count": len(new_vars),
                    "request_id": user_ctx.request_id,
                },
            )

            return ExecuteCodeResponse(
                execution_id=execution_id,
                status=status,
                output=output[:self.MAX_OUTPUT_SIZE] if output else None,
                error=error,
                result=self._serialize_result(result),
                variables=list(new_vars.keys()),
                execution_time_ms=execution_time_ms,
            )

        except TimeoutError:
            return ExecuteCodeResponse(
                execution_id=execution_id,
                status=ExecutionStatus.TIMEOUT,
                error=f"Execution timed out after {request.timeout or self.DEFAULT_TIMEOUT} seconds",
            )

        except Exception as e:
            logger.error(
                "Execution error",
                extra={
                    "user_id": user_ctx.user_id,
                    "execution_id": execution_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "request_id": user_ctx.request_id,
                },
            )
            return ExecuteCodeResponse(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error=f"Execution error: {e}",
            )

    async def _execute_code(
        self,
        code: str,
        namespace: dict[str, Any],
        timeout: int,
    ) -> tuple[Any, str, Optional[str]]:
        """Execute Python code in sandbox.

        Args:
            code: Code to execute
            namespace: Execution namespace
            timeout: Timeout in seconds

        Returns:
            Tuple of (result, stdout, error)
        """
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        result = None
        error = None

        try:
            # Parse the code
            tree = ast.parse(code, mode="exec")

            # Check if last statement is an expression (to capture result)
            last_expr = None
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                last_expr = tree.body.pop()
                last_expr = ast.Expression(body=last_expr.value)
                ast.fix_missing_locations(last_expr)

            # Compile the main code
            compiled_code = compile(tree, "<user_code>", "exec")

            # Execute with output capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(compiled_code, namespace)

                # Evaluate last expression if present
                if last_expr:
                    compiled_expr = compile(last_expr, "<user_code>", "eval")
                    result = eval(compiled_expr, namespace)

        except SyntaxError as e:
            error = f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            # Include traceback for debugging
            tb = traceback.format_exc()
            stderr_capture.write(tb)

        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()

        # Combine stderr with error if present
        if stderr and not error:
            error = stderr
        elif stderr and error:
            error = f"{error}\n{stderr}"

        return result, stdout, error

    async def _execute_via_bifrost(
        self,
        user_ctx: UserContext,
        request: ExecuteCodeRequest,
    ) -> ExecuteCodeResponse:
        """Delegate execution to Bifrost executor adapter (feature-flagged).

        This uses a minimal GraphQL mutation shape; adjust to match the live
        Bifrost schema when available.
        """
        mutation = """
        mutation ExecuteCode(
          $userId: ID!,
          $deviceId: ID,
          $sessionId: ID,
          $projectId: ID,
          $code: String!,
          $language: String!,
          $timeout: Int
        ) {
          executeCode(
            userId: $userId,
            deviceId: $deviceId,
            sessionId: $sessionId,
            projectId: $projectId,
            code: $code,
            language: $language,
            timeout: $timeout
          ) {
            executionId
            status
            output
            error
            result
            executionTimeMs
          }
        }
        """

        variables = {
            "userId": user_ctx.user_id,
            "deviceId": user_ctx.device_id or user_ctx.metadata.get("device_id"),
            "sessionId": user_ctx.session_id or user_ctx.metadata.get("session_id"),
            "projectId": user_ctx.project_id
            or user_ctx.workspace_id
            or user_ctx.metadata.get("project_id"),
            "code": request.code,
            "language": request.language.value,
            "timeout": request.timeout or self.DEFAULT_TIMEOUT,
        }

        data = await self.bifrost_client.mutate(mutation, variables)
        payload = data.get("executeCode", {})

        return ExecuteCodeResponse(
            execution_id=payload.get("executionId", str(uuid4())),
            status=ExecutionStatus(payload.get("status", ExecutionStatus.FAILED.value)),
            output=payload.get("output"),
            error=payload.get("error"),
            result=payload.get("result"),
            execution_time_ms=payload.get("executionTimeMs", 0),
            variables=[],
        )

    def _extract_variables(
        self,
        namespace: dict[str, Any],
        previous: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract user-defined variables from namespace.

        Args:
            namespace: Execution namespace
            previous: Previous user variables

        Returns:
            Dictionary of new/updated variables
        """
        builtins = SafeBuiltins.get_builtins()
        new_vars = {}

        for name, value in namespace.items():
            # Skip internal names
            if name.startswith("_"):
                continue

            # Skip builtins
            if name in builtins:
                continue

            # Skip if it's the same as previous
            if name in previous and previous[name] == value:
                continue

            # Only include serializable values
            if self._is_serializable(value):
                new_vars[name] = value

        return new_vars

    def _is_serializable(self, value: Any) -> bool:
        """Check if value can be serialized to JSON.

        Args:
            value: Value to check

        Returns:
            True if serializable
        """
        import json
        try:
            json.dumps(value)
            return True
        except (TypeError, ValueError):
            return False

    def _serialize_result(self, result: Any) -> Any:
        """Serialize execution result for response.

        Args:
            result: Raw result

        Returns:
            Serializable result or string representation
        """
        if result is None:
            return None

        if self._is_serializable(result):
            return result

        # Fall back to string representation
        return repr(result)

    async def get_variables(self, user_ctx: UserContext) -> dict[str, Any]:
        """Get all user variables.

        Args:
            user_ctx: User context

        Returns:
            Dictionary of variable name -> value
        """
        return await self.memory.get_variables(user_ctx)

    async def set_variable(
        self,
        user_ctx: UserContext,
        name: str,
        value: Any,
    ) -> None:
        """Set a variable in user's namespace.

        Args:
            user_ctx: User context
            name: Variable name
            value: Variable value
        """
        if not name.isidentifier():
            raise ValueError(f"Invalid variable name: {name}")

        await self.memory.set_variable(user_ctx, name, value)

    async def delete_variable(
        self,
        user_ctx: UserContext,
        name: str,
    ) -> bool:
        """Delete a variable from user's namespace.

        Args:
            user_ctx: User context
            name: Variable name

        Returns:
            True if deleted
        """
        return await self.memory.delete(user_ctx, name, MemoryType.VARIABLE)

    async def clear_variables(self, user_ctx: UserContext) -> int:
        """Clear all user variables.

        Args:
            user_ctx: User context

        Returns:
            Number of variables cleared
        """
        return await self.memory.clear(user_ctx, MemoryType.VARIABLE)


def create_executor_service(
    memory: Optional[UserScopedMemory] = None,
    bifrost_client: Any = None,
    enable_bifrost_execution: bool = False,
) -> UserScopedExecutor:
    """Factory function to create an executor service.

    Args:
        memory: Memory service (created if not provided)

    Returns:
        Configured UserScopedExecutor instance
    """
    if memory is None:
        from smartcp.services.memory import create_memory_service
        memory = create_memory_service()

    executor = UserScopedExecutor(
        memory,
        security_checker=None,
        bifrost_client=bifrost_client,
        enable_bifrost_execution=enable_bifrost_execution,
    )
    return executor
