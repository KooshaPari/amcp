"""Core executor orchestration and user-scoped execution service.

Main UserScopedExecutor class that coordinates security checking, code
execution, memory management, and result handling.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from smartcp.services.models import (
    ExecuteCodeRequest,
    ExecuteCodeResponse,
    ExecutionLanguage,
    ExecutionStatus,
    UserContext,
)
from smartcp.services.memory import MemoryType, UserScopedMemory

from .sandboxing import SafeBuiltins, SecurityChecker
from .subprocess import SubprocessManager
from .results import ExecutionResult, ResultSerializer, VariableExtractor

logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        memory: UserScopedMemory,
        security_checker: Optional[SecurityChecker] = None,
        bifrost_client: Any = None,
        allow_local_fallback: bool = False,
    ):
        """Initialize executor.

        Args:
            memory: User-scoped memory service
            security_checker: Security checker (default SecurityChecker)
            bifrost_client: Optional Bifrost client for delegated execution
        """
        self.memory = memory
        self.security = security_checker or SecurityChecker()
        self.bifrost_client = bifrost_client
        self.allow_local_fallback = allow_local_fallback
        self.subprocess_manager = SubprocessManager()

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
        if not self.bifrost_client:
            return ExecuteCodeResponse(
                execution_id=str(uuid4()),
                status=ExecutionStatus.FAILED,
                error="Bifrost client missing; SmartCP is stateless and must delegate execution",
            )

        try:
            return await self._execute_via_bifrost(user_ctx, request)
        except Exception as exc:  # noqa: BLE001
            if not self.allow_local_fallback:
                logger.error(
                    "Bifrost execution failed; local fallback disabled",
                    extra={
                        "error": str(exc),
                        "user_id": user_ctx.user_id,
                        "request_id": user_ctx.request_id,
                    },
                )
                return ExecuteCodeResponse(
                    execution_id=str(uuid4()),
                    status=ExecutionStatus.FAILED,
                    error=f"Bifrost execution failed: {exc}",
                )
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
            result, output, error = await self.subprocess_manager.run_code(
                request.code,
                namespace,
                timeout=request.timeout,
            )

            # Extract and save new/updated variables
            new_vars = VariableExtractor.extract_variables(
                namespace, user_vars, SafeBuiltins.get_builtins()
            )
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

            max_output = self.subprocess_manager.get_max_output_size()
            return ExecuteCodeResponse(
                execution_id=execution_id,
                status=status,
                output=output[:max_output] if output else None,
                error=error,
                result=ResultSerializer.serialize_result(result),
                variables=list(new_vars.keys()),
                execution_time_ms=execution_time_ms,
            )

        except TimeoutError:
            default_timeout = self.subprocess_manager.get_default_timeout()
            return ExecuteCodeResponse(
                execution_id=execution_id,
                status=ExecutionStatus.TIMEOUT,
                error=f"Execution timed out after {request.timeout or default_timeout} seconds",
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

    async def _execute_via_bifrost(
        self,
        user_ctx: UserContext,
        request: ExecuteCodeRequest,
    ) -> ExecuteCodeResponse:
        """Delegate execution to Bifrost via executeTool mutation (with fallback)."""
        mutation = """
        mutation ExecuteTool(
          $toolId: ID!,
          $parameters: String!,
          $context: String
        ) {
          executeTool(input: {
            toolId: $toolId,
            parameters: $parameters,
            context: $context
          }) {
            success
            toolId
            output
            error
            executionTime
            metadata
          }
        }
        """

        payload = {
            "user_id": user_ctx.user_id,
            "device_id": user_ctx.device_id or user_ctx.metadata.get("device_id"),
            "session_id": user_ctx.session_id or user_ctx.metadata.get("session_id"),
            "project_id": user_ctx.project_id
            or user_ctx.workspace_id
            or user_ctx.metadata.get("project_id"),
            "cwd": user_ctx.cwd or user_ctx.metadata.get("cwd"),
            "code": request.code,
            "language": request.language.value,
            "timeout": request.timeout or self.subprocess_manager.get_default_timeout(),
            "context": request.context or {},
        }

        parameters_json = json.dumps(payload)
        context_json = json.dumps(user_ctx.context or user_ctx.metadata or {})

        variables = {
            "toolId": "execute_code",
            "parameters": parameters_json,
            "context": context_json,
        }

        data = await self.bifrost_client.mutate(mutation, variables)
        result = data.get("executeTool", {}) if data else {}

        status = (
            ExecutionStatus.COMPLETED
            if result.get("success")
            else ExecutionStatus.FAILED
        )

        return ExecuteCodeResponse(
            execution_id=str(uuid4()),
            status=status,
            output=result.get("output"),
            error=result.get("error"),
            result=result.get("metadata"),
            execution_time_ms=result.get("executionTime", 0),
            variables=[],
        )

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
