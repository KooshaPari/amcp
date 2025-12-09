"""Authentication Middleware for SmartCP.

Provides FastAPI middleware for bearer token authentication
with JWT validation and UserContext injection.
"""

import logging
import time
from typing import Any, Callable, Optional

from fastapi import HTTPException, Response
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

from smartcp.auth.context import (
    UserContextProvider,
    clear_request_context,
    generate_request_id,
    set_request_context,
    set_request_id,
)
from smartcp.auth.token import TokenValidator
from smartcp.auth.validators import AuthenticationValidator

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for SmartCP.

    Extracts bearer token from Authorization header, validates it,
    and injects UserContext into request state.

    This middleware supports:
    - JWT bearer tokens (validated with TokenValidator)
    - Path-based authentication bypass (e.g., health checks)
    - Request ID generation and propagation
    - Structured logging of auth events
    """

    def __init__(
        self,
        app: Any,
        token_validator: TokenValidator,
        context_provider: Optional[UserContextProvider] = None,
        skip_paths: Optional[set[str]] = None,
        require_auth: bool = True,
    ):
        """Initialize auth middleware.

        Args:
            app: FastAPI/Starlette application
            token_validator: TokenValidator for JWT validation
            context_provider: Optional UserContextProvider (created if not provided)
            skip_paths: Paths to skip authentication (e.g., {"/health", "/metrics"})
            require_auth: If True, reject requests without valid auth
        """
        super().__init__(app)
        self.token_validator = token_validator
        self.context_provider = context_provider or UserContextProvider()
        self.skip_paths = skip_paths or {"/health", "/healthz", "/metrics", "/ready"}
        self.require_auth = require_auth

        # Initialize authentication validator
        self.auth_validator = AuthenticationValidator(
            token_validator=token_validator,
            context_provider=self.context_provider,
            require_auth=require_auth,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through authentication middleware.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from downstream handler
        """
        start_time = time.perf_counter()

        # Generate request ID
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_id(request_id)

        # Get trace ID for distributed tracing
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get(
            "traceparent"
        )

        try:
            # Skip auth for configured paths
            if self._should_skip_auth(request.url.path):
                logger.debug(
                    "Skipping auth for path",
                    extra={"path": request.url.path, "request_id": request_id},
                )
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
                return response

            # Extract and validate token
            user_context = await self.auth_validator.authenticate_request(
                request, request_id, trace_id
            )

            # Store context in request state and context var
            request.state.user_context = user_context
            set_request_context(user_context)

            # Log successful auth
            logger.info(
                "Request authenticated",
                extra={
                    "user_id": user_context.user_id,
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                },
            )

            # Process request
            response = await call_next(request)

            # Add headers to response
            response.headers["X-Request-ID"] = request_id
            if trace_id:
                response.headers["X-Trace-ID"] = trace_id

            return response

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise

        except Exception as e:
            logger.error(
                "Auth middleware error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "request_id": request_id,
                    "path": request.url.path,
                },
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": "Internal authentication error",
                        "type": "internal_error",
                        "code": "auth_error",
                    }
                },
            )

        finally:
            # Clear context and log timing
            clear_request_context()
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "Request completed",
                extra={"request_id": request_id, "duration_ms": duration_ms},
            )

    def _should_skip_auth(self, path: str) -> bool:
        """Check if path should skip authentication.

        Args:
            path: Request path

        Returns:
            True if auth should be skipped
        """
        # Exact match
        if path in self.skip_paths:
            return True

        # Prefix match (for paths like /health/live, /health/ready)
        for skip_path in self.skip_paths:
            if path.startswith(skip_path + "/"):
                return True

        return False


def create_auth_middleware(
    token_validator: TokenValidator,
    context_provider: Optional[UserContextProvider] = None,
    skip_paths: Optional[set[str]] = None,
    require_auth: bool = True,
) -> type[AuthMiddleware]:
    """Factory function to create configured AuthMiddleware class.

    This is useful for FastAPI's add_middleware pattern.

    Args:
        token_validator: TokenValidator for JWT validation
        context_provider: Optional UserContextProvider
        skip_paths: Paths to skip authentication
        require_auth: If True, reject unauthenticated requests

    Returns:
        Configured AuthMiddleware class
    """

    class ConfiguredAuthMiddleware(AuthMiddleware):
        def __init__(self, app: Any):
            super().__init__(
                app=app,
                token_validator=token_validator,
                context_provider=context_provider,
                skip_paths=skip_paths,
                require_auth=require_auth,
            )

    return ConfiguredAuthMiddleware
