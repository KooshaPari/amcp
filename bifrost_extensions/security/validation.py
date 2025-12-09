"""Input and output validation for security using Pydantic."""

import re
from typing import Any, Optional
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    field_validator,
    ValidationError as PydanticValidationError,
)

from bifrost_extensions.exceptions import ValidationError

__all__ = [
    "InputValidator",
    "OutputValidator",
    "sanitize_input",
    "validate_output",
]


class InputValidator:
    """Input validation and sanitization.

    Prevents injection attacks and malformed input.
    """

    # Dangerous patterns to reject
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(;|\-\-|\/\*|\*\/)",
        r"(\b(OR|AND)\b.*=.*)",
    ]

    SCRIPT_INJECTION_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ]

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input.

        Args:
            value: Input string
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        Raises:
            ValidationError: If input invalid
        """
        if not isinstance(value, str):
            raise ValidationError(
                "Expected string input",
                details={"type": type(value).__name__},
            )

        # Check length
        if len(value) > max_length:
            raise ValidationError(
                f"Input too long (max {max_length} characters)",
                details={"length": len(value)},
            )

        # Check for SQL injection
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(
                    "Potentially malicious input detected",
                    details={"pattern": "sql_injection"},
                )

        # Check for script injection
        for pattern in InputValidator.SCRIPT_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(
                    "Potentially malicious input detected",
                    details={"pattern": "script_injection"},
                )

        # Strip control characters
        value = "".join(
            char for char in value if ord(char) >= 32 or char in "\n\r\t"
        )

        return value.strip()

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format using Pydantic.

        Args:
            email: Email address

        Returns:
            Validated email

        Raises:
            ValidationError: If email invalid
        """
        try:
            # Use Pydantic's EmailStr validator
            class EmailModel(BaseModel):
                email: EmailStr

            EmailModel(email=email)
            return email.lower()
        except PydanticValidationError as e:
            raise ValidationError(
                "Invalid email format", details={"email": email}
            )

    @staticmethod
    def validate_url(
        url: str, allowed_schemes: Optional[list[str]] = None
    ) -> str:
        """Validate URL format and scheme.

        Args:
            url: URL to validate
            allowed_schemes: Allowed URL schemes (default: http, https)

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL invalid
        """
        if allowed_schemes is None:
            allowed_schemes = ["http", "https"]

        try:
            parsed = urlparse(url)
            if parsed.scheme not in allowed_schemes:
                raise ValidationError(
                    f"Invalid URL scheme (allowed: {allowed_schemes})",
                    details={"scheme": parsed.scheme},
                )
            if not parsed.netloc:
                raise ValidationError("Invalid URL (missing host)")
            return url
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid URL: {e}")

    @staticmethod
    def validate_json_schema(data: dict, schema: dict) -> None:
        """Validate JSON against schema using jsonschema.

        Args:
            data: JSON data to validate
            schema: JSON schema

        Raises:
            ValidationError: If validation fails
        """
        try:
            import jsonschema

            jsonschema.validate(data, schema)
        except ImportError:
            raise ValidationError(
                "jsonschema package required for schema validation"
            )
        except Exception as e:
            raise ValidationError(f"Schema validation failed: {e}")


class OutputValidator:
    """Output validation before returning to client.

    Ensures sensitive data not leaked.
    """

    SENSITIVE_KEYS = {
        "api_key",
        "secret",
        "password",
        "token",
        "private_key",
        "credential",
        "auth",
    }

    @staticmethod
    def redact_sensitive(
        data: Any, keys_to_redact: Optional[set[str]] = None
    ) -> Any:
        """Redact sensitive fields from output.

        Args:
            data: Data to redact
            keys_to_redact: Additional keys to redact

        Returns:
            Data with sensitive fields redacted
        """
        if keys_to_redact is None:
            keys_to_redact = OutputValidator.SENSITIVE_KEYS

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Check if key contains sensitive words
                if any(
                    sensitive in key.lower() for sensitive in keys_to_redact
                ):
                    result[key] = "***REDACTED***"
                else:
                    result[key] = OutputValidator.redact_sensitive(
                        value, keys_to_redact
                    )
            return result

        elif isinstance(data, list):
            return [
                OutputValidator.redact_sensitive(item, keys_to_redact)
                for item in data
            ]

        return data

    @staticmethod
    def validate_response_size(
        data: Any, max_size: int = 10 * 1024 * 1024
    ) -> None:
        """Validate response size to prevent memory issues.

        Args:
            data: Response data
            max_size: Maximum size in bytes

        Raises:
            ValidationError: If response too large
        """
        import sys

        size = sys.getsizeof(data)
        if size > max_size:
            raise ValidationError(
                f"Response too large ({size} bytes, max {max_size})",
                details={"size": size, "max_size": max_size},
            )


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Convenience function for input sanitization.

    Args:
        value: Input string
        max_length: Maximum length

    Returns:
        Sanitized string
    """
    return InputValidator.sanitize_string(value, max_length)


def validate_output(data: Any, redact: bool = True) -> Any:
    """Convenience function for output validation.

    Args:
        data: Output data
        redact: Whether to redact sensitive fields

    Returns:
        Validated/redacted output
    """
    # Validate size
    OutputValidator.validate_response_size(data)

    # Redact if requested
    if redact:
        data = OutputValidator.redact_sensitive(data)

    return data
