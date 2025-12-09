"""Resource Access Enforcement Middleware.

Enforces that all resource access in SmartCP goes through Bifrost client.
Prevents direct database imports (supabase, neo4j, redis, qdrant) and
ensures all resource calls use the bifrost_client abstraction.

This middleware implements Phase 5.1 of the remediation specification:
"Add Bifrost Delegation Enforcement" to prevent stateful DB access.
"""

import inspect
import logging
import sys
from typing import Any, Callable, Optional, Set

from fastapi import HTTPException, Response
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ResourceAccessEnforcementMiddleware(BaseHTTPMiddleware):
    """Enforce Bifrost delegation for all resource access.

    This middleware ensures that:
    1. No direct DB imports (supabase, neo4j, redis, qdrant) in smartcp/
    2. All resource access uses bifrost_client
    3. Violations are logged and can be enforced

    Violations are caught early via static analysis (ruff) and logged
    at runtime via this middleware for defense-in-depth.
    """

    # Forbidden module imports (should only appear in bifrost-extensions)
    FORBIDDEN_MODULES = {
        "supabase",
        "neo4j",
        "redis",
        "qdrant_client",
    }

    # Bifrost client module that all resource access should use
    APPROVED_RESOURCE_CLIENT = "services.bifrost.bifrost_client"

    def __init__(
        self,
        app: Any,
        enforce: bool = False,
        log_violations: bool = True,
    ):
        """Initialize resource access enforcement middleware.

        Args:
            app: FastAPI/Starlette application
            enforce: If True, reject requests with violations (fail-fast)
                   If False, only log violations (audit mode)
            log_violations: If True, log all access violations
        """
        super().__init__(app)
        self.enforce = enforce
        self.log_violations = log_violations
        self._forbidden_modules_loaded = set()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through resource access enforcement.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from downstream handler, or 403 if violation detected
        """
        # Check for forbidden modules in current execution context
        violations = self._check_forbidden_imports()

        if violations:
            self._log_violation(request, violations)
            if self.enforce:
                raise HTTPException(
                    status_code=403,
                    detail="Resource access violation: direct DB imports detected",
                )

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log any unexpected errors
            logger.error(
                f"Error in resource access enforcement: {e}",
                extra={"request_path": request.url.path},
            )
            raise

    def _check_forbidden_imports(self) -> Set[str]:
        """Check if any forbidden modules are currently loaded.

        Returns:
            Set of forbidden module names that are loaded
        """
        violations = set()

        for module_name in self.FORBIDDEN_MODULES:
            if module_name in sys.modules:
                # Check if it's being used in smartcp/ (not bifrost-extensions)
                module = sys.modules.get(module_name)
                if module and self._is_smartcp_context(module):
                    if module_name not in self._forbidden_modules_loaded:
                        violations.add(module_name)
                        self._forbidden_modules_loaded.add(module_name)

        return violations

    def _is_smartcp_context(self, module: Any) -> bool:
        """Determine if module was loaded from smartcp/ context.

        Args:
            module: Python module to check

        Returns:
            True if module loaded in smartcp context, False otherwise
        """
        try:
            # Get the file path of the module
            if hasattr(module, "__file__") and module.__file__:
                file_path = module.__file__
                # Check if it was loaded from smartcp (not bifrost-extensions)
                return (
                    "smartcp" in file_path
                    and "bifrost-extensions" not in file_path
                )
        except Exception:
            pass

        return False

    def _log_violation(self, request: Request, violations: Set[str]) -> None:
        """Log resource access violation.

        Args:
            request: The HTTP request that triggered the violation
            violations: Set of forbidden modules loaded
        """
        if not self.log_violations:
            return

        violation_list = ", ".join(sorted(violations))
        logger.warning(
            "Resource access violation detected",
            extra={
                "request_path": request.url.path,
                "method": request.method,
                "forbidden_modules": violation_list,
                "enforcement": "strict" if self.enforce else "audit",
                "remediation": (
                    "Import all database resources through "
                    f"{self.APPROVED_RESOURCE_CLIENT}"
                ),
            },
        )

    @staticmethod
    def validate_bifrost_client_usage(func: Callable) -> bool:
        """Validate that a function uses bifrost_client for resource access.

        This is a helper for static validation and testing.

        Args:
            func: Function to validate

        Returns:
            True if bifrost_client is referenced in function, False otherwise
        """
        try:
            source = inspect.getsource(func)
            return "bifrost_client" in source
        except Exception:
            return False


def create_resource_enforcement_middleware(
    enforce: bool = False,
    log_violations: bool = True,
) -> Callable:
    """Factory function to create resource enforcement middleware.

    Args:
        enforce: If True, reject requests with violations
        log_violations: If True, log all violations

    Returns:
        Configured middleware factory
    """

    def factory(app: Any) -> ResourceAccessEnforcementMiddleware:
        return ResourceAccessEnforcementMiddleware(
            app=app,
            enforce=enforce,
            log_violations=log_violations,
        )

    return factory
