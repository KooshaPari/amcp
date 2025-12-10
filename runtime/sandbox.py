"""SmartCP Sandbox Wrapper.

Wrapper around LangChain Sandbox (Pyodide WASM) for secure code execution.
Provides session management and namespace injection.
"""

import asyncio
import logging
import time
from typing import Any

from smartcp.runtime.types import ExecutionStatus, SandboxResult

logger = logging.getLogger(__name__)


class SandboxWrapper:
    """Wrapper around LangChain Sandbox with session management.

    Uses Pyodide (WebAssembly Python) for true isolation:
    - No filesystem access to host
    - No network access (unless explicitly enabled)
    - Memory limits enforced
    - Timeout protection

    Falls back to restricted local execution if langchain-sandbox unavailable.
    """

    def __init__(self):
        """Initialize sandbox wrapper."""
        self._sandbox: Any = None
        self._session_bytes: bytes | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the sandbox environment."""
        if self._initialized:
            return

        try:
            from langchain_sandbox import PyodideSandbox

            self._sandbox = PyodideSandbox()
            await self._sandbox.__aenter__()
            self._initialized = True
            logger.info("LangChain Sandbox initialized (Pyodide WASM)")
        except ImportError:
            logger.warning(
                "langchain-sandbox not available, using restricted fallback execution"
            )
            self._sandbox = None
            self._initialized = True

    async def close(self) -> None:
        """Clean up sandbox resources."""
        if self._sandbox is not None:
            try:
                await self._sandbox.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing sandbox: {e}")
        self._initialized = False
        self._sandbox = None

    async def execute(
        self,
        code: str,
        namespace: dict[str, Any] | None = None,
        session: bytes | None = None,
        timeout: int | None = None,
    ) -> SandboxResult:
        """Execute code in the sandbox.

        Args:
            code: Python code to execute
            namespace: Global namespace to inject
            session: Previous session state bytes to restore
            timeout: Execution timeout (overrides config)

        Returns:
            SandboxResult with execution output and state
        """
        if not self._initialized:
            await self.initialize()

        timeout = timeout or 30
        namespace = namespace or {}

        # Restore session if provided
        if session is not None:
            self._session_bytes = session

        start_time = time.time()

        if self._sandbox is not None:
            return await self._execute_pyodide(code, namespace, timeout, start_time)
        else:
            return await self._execute_fallback(code, namespace, timeout, start_time)

    async def _execute_pyodide(
        self,
        code: str,
        namespace: dict[str, Any],
        timeout: int,
        start_time: float,
    ) -> SandboxResult:
        """Execute code using Pyodide sandbox."""
        try:
            # Prepare code with namespace injection
            setup_code = self._build_setup_code(namespace)
            full_code = f"{setup_code}\n{code}"

            # Execute in sandbox
            result = await asyncio.wait_for(
                self._sandbox.arun(full_code),
                timeout=timeout,
            )

            execution_time_ms = (time.time() - start_time) * 1000

            return SandboxResult(
                stdout=result.stdout if hasattr(result, "stdout") else str(result),
                stderr=result.stderr if hasattr(result, "stderr") else "",
                return_value=result.result if hasattr(result, "result") else result,
                execution_time_ms=execution_time_ms,
                status=ExecutionStatus.COMPLETED,
            )

        except asyncio.TimeoutError:
            execution_time_ms = (time.time() - start_time) * 1000
            return SandboxResult(
                stderr=f"Execution timed out after {timeout} seconds",
                execution_time_ms=execution_time_ms,
                status=ExecutionStatus.TIMEOUT,
            )
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Sandbox execution error: {e}")
            return SandboxResult(
                stderr=str(e),
                execution_time_ms=execution_time_ms,
                status=ExecutionStatus.FAILED,
            )

    async def _execute_fallback(
        self,
        code: str,
        namespace: dict[str, Any],
        timeout: int,
        start_time: float,
    ) -> SandboxResult:
        """Fallback execution when Pyodide is not available.

        Uses restricted exec() with filtered builtins.
        WARNING: Less secure than Pyodide, use only for development.
        """
        import io
        from contextlib import redirect_stderr, redirect_stdout

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Build restricted globals
        restricted_globals = self._build_restricted_globals(namespace)

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute with timeout
                exec_result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: exec(code, restricted_globals),
                    ),
                    timeout=timeout,
                )

            execution_time_ms = (time.time() - start_time) * 1000

            # Extract return value if code ends with expression
            return_value = restricted_globals.get("__result__", exec_result)

            return SandboxResult(
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                return_value=return_value,
                execution_time_ms=execution_time_ms,
                status=ExecutionStatus.COMPLETED,
            )

        except asyncio.TimeoutError:
            execution_time_ms = (time.time() - start_time) * 1000
            return SandboxResult(
                stderr=f"Execution timed out after {timeout} seconds",
                execution_time_ms=execution_time_ms,
                status=ExecutionStatus.TIMEOUT,
            )
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return SandboxResult(
                stdout=stdout_capture.getvalue(),
                stderr=f"{type(e).__name__}: {e}",
                execution_time_ms=execution_time_ms,
                status=ExecutionStatus.FAILED,
            )

    def _build_setup_code(self, namespace: dict[str, Any]) -> str:
        """Build setup code for namespace injection in Pyodide."""
        # For Pyodide, we serialize namespace items that can be JSON encoded
        # Complex objects (functions, classes) are handled differently
        lines = []
        for name, value in namespace.items():
            if callable(value):
                # Skip callables - they need special handling in Pyodide
                continue
            try:
                import json

                json_value = json.dumps(value)
                lines.append(f"{name} = {json_value}")
            except (TypeError, ValueError):
                # Skip non-serializable values
                continue
        return "\n".join(lines)

    def _build_restricted_globals(self, namespace: dict[str, Any]) -> dict[str, Any]:
        """Build restricted globals for fallback execution."""
        # Start with safe builtins
        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "bytes": bytes,
            "callable": callable,
            "chr": chr,
            "dict": dict,
            "divmod": divmod,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "format": format,
            "frozenset": frozenset,
            "getattr": getattr,
            "hasattr": hasattr,
            "hash": hash,
            "hex": hex,
            "id": id,
            "int": int,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "iter": iter,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "next": next,
            "oct": oct,
            "ord": ord,
            "pow": pow,
            "print": print,
            "range": range,
            "repr": repr,
            "reversed": reversed,
            "round": round,
            "set": set,
            "slice": slice,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,
            # Explicitly blocked: open, exec, eval, compile, __import__, etc.
        }

        restricted_globals = {
            "__builtins__": safe_builtins,
            "__name__": "__main__",
        }

        # Add namespace items
        restricted_globals.update(namespace)

        return restricted_globals

    def get_session(self) -> bytes | None:
        """Get current session state for persistence.

        Returns:
            Session bytes to store, or None if no session
        """
        return self._session_bytes

    def load_session(self, session_bytes: bytes) -> None:
        """Load a previous session state.

        Args:
            session_bytes: Previously saved session state
        """
        self._session_bytes = session_bytes

    async def __aenter__(self) -> "SandboxWrapper":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
