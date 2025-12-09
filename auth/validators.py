"""Token and session validation for authentication.

Provides validation logic for bearer tokens and session extraction.
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status

from smartcp.auth.context import UserContextProvider
from smartcp.auth.token import TokenValidationError, TokenValidator
from smartcp.services.models import UserContext

logger = logging.getLogger(__name__)


class AuthenticationValidator:
    """Validates authentication tokens and creates user contexts.

    Handles:
    - Bearer token extraction from Authorization header
    - JWT token validation
    - UserContext creation from token payload
    - Anonymous user context creation
    """

    def __init__(
        self,
        token_validator: TokenValidator,
        context_provider: Optional[UserContextProvider] = None,
        require_auth: bool = True,
    ):
        """Initialize authentication validator.

        Args:
            token_validator: TokenValidator for JWT validation
            context_provider: Optional UserContextProvider (created if not provided)
            require_auth: If True, reject requests without valid auth
        """
        self.token_validator = token_validator
        self.context_provider = context_provider or UserContextProvider()
        self.require_auth = require_auth

    async def authenticate_request(
        self, request: Request, request_id: str, trace_id: Optional[str]
    ) -> UserContext:
        """Authenticate request and extract UserContext.

        Args:
            request: Incoming request
            request_id: Request ID for logging
            trace_id: Optional trace ID

        Returns:
            UserContext extracted from token

        Raises:
            HTTPException: If authentication fails
        """
        # Get Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            if self.require_auth:
                logger.warning(
                    "Missing Authorization header",
                    extra={"request_id": request_id, "path": request.url.path},
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": {
                            "message": "Missing Authorization header",
                            "type": "authentication_error",
                            "code": "missing_auth",
                        }
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            # Return anonymous context if auth not required
            return self.context_provider.anonymous(
                request_id=request_id, trace_id=trace_id
            )

        # Validate Bearer format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(
                "Invalid Authorization header format",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "message": "Invalid Authorization header format. Expected: Bearer <token>",
                        "type": "authentication_error",
                        "code": "invalid_auth_format",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]

        try:
            # Validate token
            payload = self.token_validator.validate(token)

            device_id = request.headers.get("X-Device-ID")
            session_id = request.headers.get("X-Session-ID")
            project_id = request.headers.get("X-Project-ID")
            cwd = request.headers.get("X-Project-Cwd")
            context_data = {}
            raw_context = request.headers.get("X-Context")
            if raw_context:
                try:
                    import json
                    context_data = json.loads(raw_context)
                except Exception:
                    context_data = {}

            # Create UserContext from payload
            return self.context_provider.from_token_payload(
                payload=payload,
                request_id=request_id,
                trace_id=trace_id,
                device_id=device_id,
                session_id=session_id,
                project_id=project_id,
                cwd=cwd,
                context_data=context_data,
            )

        except TokenValidationError as e:
            logger.warning(
                "Token validation failed",
                extra={
                    "error": e.message,
                    "code": e.code,
                    "request_id": request_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "message": e.message,
                        "type": "authentication_error",
                        "code": e.code.lower(),
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )


def extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """Extract bearer token from Authorization header.

    Args:
        auth_header: Authorization header value

    Returns:
        Bearer token if valid format, None otherwise
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def validate_auth_header_format(auth_header: str) -> bool:
    """Validate Authorization header format.

    Args:
        auth_header: Authorization header value

    Returns:
        True if format is valid (Bearer <token>)
    """
    parts = auth_header.split()
    return len(parts) == 2 and parts[0].lower() == "bearer"
