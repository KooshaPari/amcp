"""JWT Token Validation for SmartCP.

Provides JWT token validation with configurable algorithms and claims.
Supports Supabase JWT tokens and custom JWT configurations.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class JWTConfig:
    """JWT validation configuration."""

    # Secret key or public key for verification
    secret_key: str
    # Algorithm (HS256, RS256, etc.)
    algorithm: str = "HS256"
    # Expected issuer (optional)
    issuer: Optional[str] = None
    # Expected audience (optional)
    audience: Optional[str] = None
    # Verify expiration
    verify_exp: bool = True
    # Clock skew tolerance in seconds
    leeway: int = 30


class TokenPayload(BaseModel):
    """Parsed JWT token payload."""

    # Standard claims
    sub: str = Field(..., description="Subject (user ID)")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    iat: Optional[int] = Field(None, description="Issued at timestamp")
    iss: Optional[str] = Field(None, description="Issuer")
    aud: Optional[str] = Field(None, description="Audience")

    # Supabase-specific claims
    email: Optional[str] = Field(None, description="User email")
    role: Optional[str] = Field(None, description="User role")
    app_metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="App metadata"
    )
    user_metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="User metadata"
    )

    # Custom claims
    workspace_id: Optional[str] = Field(None, description="Workspace ID")
    permissions: list[str] = Field(
        default_factory=list, description="User permissions"
    )

    @property
    def user_id(self) -> str:
        """Get user ID from subject claim."""
        return self.sub

    def is_expired(self, leeway: int = 0) -> bool:
        """Check if token is expired."""
        if self.exp is None:
            return False
        now = int(datetime.now(timezone.utc).timestamp())
        return now > (self.exp + leeway)


class TokenValidationError(Exception):
    """Token validation error."""

    def __init__(self, message: str, code: str = "INVALID_TOKEN"):
        self.message = message
        self.code = code
        super().__init__(message)


class TokenValidator:
    """JWT token validator.

    Validates bearer tokens and extracts user information.
    Supports both symmetric (HS256) and asymmetric (RS256) algorithms.
    """

    def __init__(self, config: JWTConfig):
        """Initialize token validator.

        Args:
            config: JWT configuration
        """
        self.config = config
        self._jwt_module: Optional[Any] = None

    @property
    def jwt(self) -> Any:
        """Lazy import of jwt module."""
        if self._jwt_module is None:
            try:
                import jwt

                self._jwt_module = jwt
            except ImportError as e:
                raise ImportError(
                    "PyJWT is required for token validation. "
                    "Install with: pip install PyJWT"
                ) from e
        return self._jwt_module

    def validate(self, token: str) -> TokenPayload:
        """Validate JWT token and extract payload.

        Args:
            token: JWT token string (without "Bearer " prefix)

        Returns:
            TokenPayload with extracted claims

        Raises:
            TokenValidationError: If token is invalid
        """
        try:
            # Build decode options
            options = {
                "verify_signature": True,
                "verify_exp": self.config.verify_exp,
                "verify_iss": self.config.issuer is not None,
                "verify_aud": self.config.audience is not None,
                "require": ["sub"],
            }

            # Decode and verify token
            payload = self.jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience,
                leeway=self.config.leeway,
                options=options,
            )

            # Parse payload into structured object
            return self._parse_payload(payload)

        except self.jwt.ExpiredSignatureError as e:
            logger.warning("Token expired", extra={"error": str(e)})
            raise TokenValidationError("Token has expired", "TOKEN_EXPIRED") from e

        except self.jwt.InvalidIssuerError as e:
            logger.warning("Invalid issuer", extra={"error": str(e)})
            raise TokenValidationError("Invalid token issuer", "INVALID_ISSUER") from e

        except self.jwt.InvalidAudienceError as e:
            logger.warning("Invalid audience", extra={"error": str(e)})
            raise TokenValidationError(
                "Invalid token audience", "INVALID_AUDIENCE"
            ) from e

        except self.jwt.DecodeError as e:
            logger.warning("Token decode error", extra={"error": str(e)})
            raise TokenValidationError("Invalid token format", "DECODE_ERROR") from e

        except self.jwt.InvalidTokenError as e:
            logger.warning("Invalid token", extra={"error": str(e)})
            raise TokenValidationError("Invalid token", "INVALID_TOKEN") from e

        except Exception as e:
            logger.error(
                "Unexpected token validation error",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise TokenValidationError(
                "Token validation failed", "VALIDATION_ERROR"
            ) from e

    def _parse_payload(self, payload: dict[str, Any]) -> TokenPayload:
        """Parse raw JWT payload into TokenPayload model.

        Args:
            payload: Raw JWT payload dictionary

        Returns:
            Structured TokenPayload
        """
        # Extract standard claims
        result = {
            "sub": payload["sub"],
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "iss": payload.get("iss"),
            "aud": payload.get("aud") if isinstance(payload.get("aud"), str) else None,
        }

        # Extract Supabase-specific claims
        result["email"] = payload.get("email")
        result["role"] = payload.get("role")
        result["app_metadata"] = payload.get("app_metadata", {})
        result["user_metadata"] = payload.get("user_metadata", {})

        # Extract custom claims
        result["workspace_id"] = payload.get("workspace_id") or payload.get(
            "app_metadata", {}
        ).get("workspace_id")

        # Build permissions from role and app_metadata
        permissions = []
        if payload.get("role"):
            permissions.append(f"role:{payload['role']}")
        if payload.get("app_metadata", {}).get("permissions"):
            permissions.extend(payload["app_metadata"]["permissions"])
        result["permissions"] = permissions

        return TokenPayload(**result)

    def decode_unverified(self, token: str) -> dict[str, Any]:
        """Decode token without verification (for debugging only).

        Args:
            token: JWT token string

        Returns:
            Raw payload dictionary

        Warning:
            This method should only be used for debugging.
            Never use in production code paths.
        """
        return self.jwt.decode(token, options={"verify_signature": False})


def create_token_validator(
    secret_key: str,
    algorithm: str = "HS256",
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> TokenValidator:
    """Create a token validator with the given configuration.

    Args:
        secret_key: Secret key for token verification
        algorithm: JWT algorithm (default: HS256)
        issuer: Expected issuer (optional)
        audience: Expected audience (optional)

    Returns:
        Configured TokenValidator instance
    """
    config = JWTConfig(
        secret_key=secret_key,
        algorithm=algorithm,
        issuer=issuer,
        audience=audience,
    )
    return TokenValidator(config)
