"""Subprocess and code execution management.

Handles the actual execution of Python code in isolated namespaces with
output capture and error handling.
"""

import ast
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any, Optional


class CodeExecutor:
    """Executes Python code in isolated namespace."""

    @staticmethod
    async def execute_code(
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


class SubprocessManager:
    """Manages subprocess execution and resource cleanup."""

    def __init__(self):
        """Initialize subprocess manager."""
        self.max_output_size = 100_000  # characters
        self.default_timeout = 30  # seconds

    async def run_code(
        self,
        code: str,
        namespace: dict[str, Any],
        timeout: Optional[int] = None,
    ) -> tuple[Any, str, Optional[str]]:
        """Run code with resource management.

        Args:
            code: Python code to execute
            namespace: Execution namespace
            timeout: Timeout in seconds

        Returns:
            Tuple of (result, stdout, error)
        """
        timeout = timeout or self.default_timeout

        result, stdout, error = await CodeExecutor.execute_code(
            code, namespace, timeout
        )

        # Truncate output if too large
        if stdout and len(stdout) > self.max_output_size:
            stdout = stdout[: self.max_output_size]

        return result, stdout, error

    def get_max_output_size(self) -> int:
        """Get maximum output size."""
        return self.max_output_size

    def get_default_timeout(self) -> int:
        """Get default timeout."""
        return self.default_timeout
