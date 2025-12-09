"""Exceptions for Bifrost Extensions SDK."""


class BifrostError(Exception):
    """Base exception for Bifrost SDK."""

    def __init__(
        self,
        message: str,
        error_code: str = "BIFROST_ERROR",
        details: dict | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with code and details."""
        msg = f"[{self.error_code}] {self.message}"
        if self.details:
            msg += f"\nDetails: {self.details}"
        return msg


class RoutingError(BifrostError):
    """Error during routing operation."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, "ROUTING_ERROR", details)


class ValidationError(BifrostError):
    """Invalid request parameters."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class TimeoutError(BifrostError):
    """Operation timed out."""

    def __init__(self, message: str, timeout_ms: float):
        super().__init__(
            message, "TIMEOUT_ERROR", {"timeout_ms": timeout_ms}
        )


class AuthenticationError(BifrostError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed", details: dict | None = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class ModelNotFoundError(BifrostError):
    """No suitable model found."""

    def __init__(self, message: str, constraints: dict | None = None):
        super().__init__(
            message, "MODEL_NOT_FOUND", {"constraints": constraints}
        )


class RateLimitError(BifrostError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict | None = None,
    ):
        if details is None:
            details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR", details)
