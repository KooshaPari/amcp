"""Request Context Management for SmartCP.

Provides async-safe context management for UserContext propagation
through the request lifecycle in HTTP stateless mode.
"""

import logging
from contextvars import ContextVar
from typing import Any, Optional
from uuid import uuid4

from smartcp.services.models import UserContext

logger = logging.getLogger(__name__)

# Context variable for request-scoped UserContext
_request_context: ContextVar[Optional[UserContext]] = ContextVar(
    "smartcp_user_context", default=None
)

# Context variable for request ID
_request_id: ContextVar[Optional[str]] = ContextVar("smartcp_request_id", default=None)


def get_request_context() -> Optional[UserContext]:
    """Get the current request's UserContext.

    Returns:
        UserContext if set, None otherwise
    """
    return _request_context.get()


def set_request_context(context: UserContext) -> None:
    """Set the UserContext for the current request.

    Args:
        context: UserContext to set
    """
    _request_context.set(context)


def clear_request_context() -> None:
    """Clear the UserContext for the current request."""
    _request_context.set(None)


def get_request_id() -> Optional[str]:
    """Get the current request ID.

    Returns:
        Request ID if set, None otherwise
    """
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current request.

    Args:
        request_id: Request ID to set
    """
    _request_id.set(request_id)


def generate_request_id() -> str:
    """Generate a new request ID.

    Returns:
        New UUID-based request ID
    """
    return str(uuid4())


class RequestContextManager:
    """Context manager for request-scoped UserContext.

    Usage:
        async with RequestContextManager(user_context) as ctx:
            # user_context is now available via get_request_context()
            await do_work()
    """

    def __init__(
        self,
        user_context: UserContext,
        request_id: Optional[str] = None,
    ):
        """Initialize context manager.

        Args:
            user_context: UserContext for this request
            request_id: Optional request ID (generated if not provided)
        """
        self.user_context = user_context
        self.request_id = request_id or generate_request_id()
        self._previous_context: Optional[UserContext] = None
        self._previous_request_id: Optional[str] = None

    async def __aenter__(self) -> UserContext:
        """Enter context manager, setting UserContext."""
        # Save previous context (for nested contexts)
        self._previous_context = get_request_context()
        self._previous_request_id = get_request_id()

        # Set request ID on context
        self.user_context.request_id = self.request_id

        # Set new context
        set_request_context(self.user_context)
        set_request_id(self.request_id)

        logger.debug(
            "Request context set",
            extra={
                "user_id": self.user_context.user_id,
                "request_id": self.request_id,
            },
        )

        return self.user_context

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager, restoring previous context."""
        # Restore previous context
        if self._previous_context is not None:
            set_request_context(self._previous_context)
        else:
            clear_request_context()

        if self._previous_request_id is not None:
            set_request_id(self._previous_request_id)

        logger.debug(
            "Request context cleared",
            extra={"request_id": self.request_id},
        )


class UserContextProvider:
    """Provider for creating UserContext from various sources.

    Handles extraction of user information from different auth providers
    (Supabase, custom JWT, API keys, etc.).
    """

    def __init__(
        self,
        default_permissions: Optional[list[str]] = None,
        default_workspace_id: Optional[str] = None,
    ):
        """Initialize provider.

        Args:
            default_permissions: Default permissions for users
            default_workspace_id: Default workspace ID
        """
        self.default_permissions = default_permissions or []
        self.default_workspace_id = default_workspace_id

    def from_token_payload(
        self,
        payload: Any,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        device_id: Optional[str] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        cwd: Optional[str] = None,
        context_data: Optional[dict[str, Any]] = None,
    ) -> UserContext:
        """Create UserContext from a validated token payload.

        Args:
            payload: TokenPayload from JWT validation
            request_id: Optional request ID
            trace_id: Optional trace ID for distributed tracing
            device_id: Optional device identifier
            session_id: Optional session identifier
            project_id: Optional project identifier
            cwd: Optional working directory
            context_data: Optional per-request context map

        Returns:
            UserContext populated from token claims
        """
        # Build permissions list
        permissions = list(payload.permissions) if payload.permissions else []
        if self.default_permissions:
            permissions.extend(
                p for p in self.default_permissions if p not in permissions
            )

        # Build metadata
        metadata: dict[str, Any] = {}
        if payload.email:
            metadata["email"] = payload.email
        if payload.role:
            metadata["role"] = payload.role
        if payload.app_metadata:
            metadata["app_metadata"] = payload.app_metadata
        if payload.user_metadata:
            metadata["user_metadata"] = payload.user_metadata

        if device_id:
            metadata["device_id"] = device_id
        if session_id:
            metadata["session_id"] = session_id
        if project_id:
            metadata["project_id"] = project_id
        if cwd:
            metadata["cwd"] = cwd

        return UserContext(
            user_id=payload.user_id,
            device_id=device_id,
            session_id=session_id,
            project_id=project_id,
            workspace_id=payload.workspace_id or self.default_workspace_id,
            permissions=permissions,
            cwd=cwd,
            context=context_data or {},
            metadata=metadata,
            request_id=request_id,
            trace_id=trace_id,
        )

    def from_api_key(
        self,
        api_key: str,
        user_id: str,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        permissions: Optional[list[str]] = None,
    ) -> UserContext:
        """Create UserContext from an API key.

        Args:
            api_key: The API key (stored in metadata for reference)
            user_id: User ID associated with API key
            request_id: Optional request ID
            trace_id: Optional trace ID
            workspace_id: Optional workspace ID
            permissions: Optional permissions list

        Returns:
            UserContext for API key user
        """
        perms = permissions or self.default_permissions.copy()

        return UserContext(
            user_id=user_id,
            workspace_id=workspace_id or self.default_workspace_id,
            permissions=perms,
            metadata={"auth_type": "api_key", "api_key_prefix": api_key[:8] + "..."},
            request_id=request_id,
            trace_id=trace_id,
        )

    def anonymous(
        self,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> UserContext:
        """Create anonymous UserContext for unauthenticated requests.

        Args:
            request_id: Optional request ID
            trace_id: Optional trace ID

        Returns:
            UserContext for anonymous user

        Note:
            Anonymous contexts should have minimal permissions
            and be used only for public endpoints.
        """
        return UserContext(
            user_id="anonymous",
            workspace_id=None,
            permissions=["read:public"],
            metadata={"auth_type": "anonymous"},
            request_id=request_id,
            trace_id=trace_id,
        )
