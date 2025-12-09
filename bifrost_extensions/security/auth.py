"""Authentication and secret management."""

import hashlib
import hmac
import os
import secrets
from typing import Optional

from opentelemetry import trace

from bifrost_extensions.exceptions import AuthenticationError

tracer = trace.get_tracer(__name__)


class APIKeyValidator:
    """
    API key validation with constant-time comparison.

    Prevents timing attacks by using constant-time comparison.
    """

    def __init__(self, expected_key: Optional[str] = None):
        """
        Initialize validator.

        Args:
            expected_key: Expected API key. If None, reads from environment.
        """
        self.expected_key = expected_key or os.getenv("BIFROST_API_KEY")
        if not self.expected_key:
            raise ValueError(
                "API key not provided and BIFROST_API_KEY not set"
            )

    def validate(self, provided_key: Optional[str]) -> None:
        """
        Validate provided API key.

        Args:
            provided_key: API key to validate

        Raises:
            AuthenticationError: If key is invalid or missing
        """
        with tracer.start_as_current_span("auth.validate_api_key") as span:
            if not provided_key:
                span.set_attribute("auth.error", "missing_key")
                raise AuthenticationError(
                    "API key required",
                    details={"reason": "Missing API key"},
                )

            # Use constant-time comparison to prevent timing attacks
            if not secrets.compare_digest(provided_key, self.expected_key):
                span.set_attribute("auth.error", "invalid_key")
                raise AuthenticationError(
                    "Invalid API key",
                    details={"reason": "API key mismatch"},
                )

            span.set_attribute("auth.validated", True)

    def hash_key(self, key: str) -> str:
        """
        Generate secure hash of API key for logging/storage.

        Args:
            key: API key to hash

        Returns:
            SHA-256 hash of key
        """
        return hashlib.sha256(key.encode()).hexdigest()[:16]


class SecretManager:
    """
    Secure secret management.

    Handles loading and validating secrets from environment variables
    with proper error messages and no hardcoded values.
    """

    @staticmethod
    def get_required(name: str, description: str = "") -> str:
        """
        Get required secret from environment.

        Args:
            name: Environment variable name
            description: Human-readable description

        Returns:
            Secret value

        Raises:
            ValueError: If secret not found
        """
        value = os.getenv(name)
        if not value:
            desc_msg = f" ({description})" if description else ""
            raise ValueError(
                f"Required secret '{name}'{desc_msg} not found in environment"
            )
        return value

    @staticmethod
    def get_optional(name: str, default: str = "") -> str:
        """
        Get optional secret from environment.

        Args:
            name: Environment variable name
            default: Default value if not found

        Returns:
            Secret value or default
        """
        return os.getenv(name, default)

    @staticmethod
    def validate_format(value: str, pattern: str, name: str) -> None:
        """
        Validate secret format.

        Args:
            value: Secret value to validate
            pattern: Regex pattern to match
            name: Secret name for error message

        Raises:
            ValueError: If format invalid
        """
        import re

        if not re.match(pattern, value):
            raise ValueError(
                f"Invalid format for '{name}'. Expected pattern: {pattern}"
            )

    @staticmethod
    def mask_secret(value: str, visible_chars: int = 4) -> str:
        """
        Mask secret for logging.

        Args:
            value: Secret to mask
            visible_chars: Number of characters to show at end

        Returns:
            Masked secret (e.g., "****1234")
        """
        if len(value) <= visible_chars:
            return "*" * len(value)
        return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def generate_request_id() -> str:
    """
    Generate unique request ID for audit logging.

    Returns:
        32-character hex request ID
    """
    return secrets.token_hex(16)


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify HMAC signature for webhooks/callbacks.

    Args:
        payload: Request payload
        signature: Provided signature
        secret: Shared secret

    Returns:
        True if signature valid
    """
    expected = hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return secrets.compare_digest(signature, expected)
