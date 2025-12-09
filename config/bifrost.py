"""Bifrost API client configuration constants.

Consolidates hardcoded Bifrost endpoints, timeouts, and connection settings
from bifrost_client.py, http_client.py, and related modules.
"""

import os
from dataclasses import dataclass


@dataclass
class BifrostEndpoints:
    """Bifrost API endpoint URLs."""

    # Default local development endpoint
    GRAPHQL_LOCAL: str = "http://localhost:8080/graphql"

    # Alternative local endpoints (used by http_client.py)
    GRAPHQL_ALT_LOCAL: str = "http://localhost:4000/graphql"
    HTTP_SERVER_LOCAL: str = "http://localhost:8000"
    SMARTCP_ENDPOINT_LOCAL: str = "http://localhost:8001"
    OAUTH_REDIRECT_LOCAL: str = "http://localhost:8080/callback"

    # Environment variable names for endpoints
    BIFROST_URL_ENV: str = "BIFROST_URL"
    BIFROST_API_KEY_ENV: str = "BIFROST_API_KEY"
    SMARTCP_ENDPOINT_ENV: str = "SMARTCP_ENDPOINT"
    OAUTH_REDIRECT_URI_ENV: str = "OAUTH_REDIRECT_URI"

    @staticmethod
    def get_graphql_endpoint() -> str:
        """Get Bifrost GraphQL endpoint from env or default."""
        return os.getenv("BIFROST_URL", BifrostEndpoints.GRAPHQL_LOCAL)

    @staticmethod
    def get_smartcp_endpoint() -> str:
        """Get SmartCP endpoint from env or default."""
        return os.getenv("SMARTCP_ENDPOINT", BifrostEndpoints.SMARTCP_ENDPOINT_LOCAL)

    @staticmethod
    def get_oauth_redirect_uri() -> str:
        """Get OAuth redirect URI from env or default."""
        return os.getenv("OAUTH_REDIRECT_URI", BifrostEndpoints.OAUTH_REDIRECT_LOCAL)


@dataclass
class BifrostTimeouts:
    """Bifrost request timeout settings (in seconds)."""

    # Default request timeout
    DEFAULT_REQUEST: float = 30.0

    # Health check timeout (quick)
    HEALTH_CHECK: float = 5.0

    # Long-running operations
    LONG_RUNNING: float = 120.0

    # Circuit breaker recovery timeout
    CIRCUIT_BREAKER_RECOVERY: float = 60.0

    # Retry multiplier for exponential backoff
    RETRY_WAIT_MIN: int = 1
    RETRY_WAIT_MAX: int = 10
    RETRY_WAIT_MULTIPLIER: int = 1

    @staticmethod
    def get_default() -> float:
        """Get default timeout from env or constant."""
        return float(os.getenv("BIFROST_TIMEOUT_SECONDS", BifrostTimeouts.DEFAULT_REQUEST))


@dataclass
class BifrostConnections:
    """Bifrost HTTP connection pool settings."""

    # Connection pooling
    MAX_CONNECTIONS: int = 100
    MAX_KEEPALIVE_CONNECTIONS: int = 20

    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_ON_TIMEOUT: bool = True
    RETRY_ON_CONNECTION_ERROR: bool = True


@dataclass
class BifrostAuth:
    """Bifrost authentication settings."""

    # Header names
    API_KEY_HEADER: str = "Authorization"
    API_KEY_PREFIX: str = "Bearer"
    CUSTOM_API_KEY_HEADER: str = "X-API-Key"

    @staticmethod
    def get_api_key() -> str | None:
        """Get Bifrost API key from environment."""
        return os.getenv("BIFROST_API_KEY")


# Convenience instances for backward compatibility
endpoints = BifrostEndpoints()
timeouts = BifrostTimeouts()
connections = BifrostConnections()
auth = BifrostAuth()
