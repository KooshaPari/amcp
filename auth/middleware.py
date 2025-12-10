"""Authentication Middleware for SmartCP.

Provides FastAPI middleware for bearer token authentication
with JWT validation.
"""

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Optional

from fastapi import HTTPException, Response
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

from smartcp.auth.token import TokenPayload, TokenValidationError, TokenValidator

logger = logging.getLogger(__name__)

# Context variables for request tracking
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_context: ContextVar[Optional[TokenPayload]] = ContextVar("user_context", default=None)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Set the current request ID."""
    _request_id.set(request_id)


def get_user_context() -> Optional[TokenPayload]:
    """Get the current user context."""
    return _user_context.get()


def set_user_context(context: TokenPayload) -> None:
    """Set the current user context."""
    _user_context.set(context)


def clear_context() -> None:
    """Clear all context variables."""
    _request_id.set(None)
    _user_context.set(None)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for SmartCP.

    Extracts bearer token from Authorization header, validates it,
    and injects user context into request state.
    """

    def __init__(
        self,
        app: Any,
        token_validator: TokenValidator,
        skip_paths: Optional[set[str]] = None,
        require_auth: bool = True,
    ):
        """Initialize auth middleware.

        Args:
            app: FastAPI/Starlette application
            token_validator: TokenValidator for JWT validation
            skip_paths: Paths to skip authentication (e.g., {"/health", "/metrics"})
            require_auth: If True, reject requests without valid auth
        """
        super().__init__(app)
        self.token_validator = token_validator
        self.skip_paths = skip_paths or {"/health", "/healthz", "/metrics", "/ready"}
        self.require_auth = require_auth

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through authentication middleware."""
        start_time = time.perf_counter()

        # Generate request ID
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_id(request_id)

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

            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                if self.require_auth:
                    raise HTTPException(
                        status_code=401,
                        detail={"error": {"message": "Missing authorization header", "code": "MISSING_AUTH"}},
                    )
                # Allow unauthenticated if not required
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
                return response

            token = auth_header[7:]  # Remove "Bearer " prefix

            # Validate token
            try:
                user_context = self.token_validator.validate(token)
            except TokenValidationError as e:
                raise HTTPException(
                    status_code=401,
                    detail={"error": {"message": e.message, "code": e.code}},
                )

            # Store context in request state
            request.state.user_context = user_context
            set_user_context(user_context)

            logger.info(
                "Request authenticated",
                extra={
                    "user_id": user_context.user_id,
                    "request_id": request_id,
                    "path": request.url.path,
                },
            )

            # Process request
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        except HTTPException:
            raise

        except Exception as e:
            logger.error(
                "Auth middleware error",
                extra={"error": str(e), "request_id": request_id},
            )
            raise HTTPException(
                status_code=500,
                detail={"error": {"message": "Internal authentication error", "code": "AUTH_ERROR"}},
            )

        finally:
            clear_context()
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "Request completed",
                extra={"request_id": request_id, "duration_ms": duration_ms},
            )

    def _should_skip_auth(self, path: str) -> bool:
        """Check if path should skip authentication."""
        if path in self.skip_paths:
            return True
        for skip_path in self.skip_paths:
            if path.startswith(skip_path + "/"):
                return True
        return False


def create_auth_middleware(
    token_validator: TokenValidator,
    skip_paths: Optional[set[str]] = None,
    require_auth: bool = True,
) -> type[AuthMiddleware]:
    """Factory function to create configured AuthMiddleware class."""

    class ConfiguredAuthMiddleware(AuthMiddleware):
        def __init__(self, app: Any):
            super().__init__(
                app=app,
                token_validator=token_validator,
                skip_paths=skip_paths,
                require_auth=require_auth,
            )

    return ConfiguredAuthMiddleware
