"""Error handling for BifrostClient."""

import logging

logger = logging.getLogger(__name__)


class BifrostError(Exception):
    """Base exception for Bifrost client errors."""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(message)


class GraphQLError(BifrostError):
    """GraphQL operation error."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message, "GRAPHQL_ERROR")
        self.errors = errors or []


class ConnectionError(BifrostError):
    """Connection error."""

    def __init__(self, message: str):
        super().__init__(message, "CONNECTION_ERROR")


class TimeoutError(BifrostError):
    """Timeout error."""

    def __init__(self, message: str):
        super().__init__(message, "TIMEOUT_ERROR")


class ValidationError(BifrostError):
    """Input validation error."""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")
