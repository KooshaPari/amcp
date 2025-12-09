"""
FastMCP Authentication Models

OAuth flow models, PKCE challenges, device codes, and tokens.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class OAuthFlow(str, Enum):
    """OAuth flow types."""
    AUTHORIZATION_CODE = "authorization_code"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


@dataclass
class PKCEChallenge:
    """PKCE code challenge and verifier."""
    code_verifier: str
    code_challenge: str
    code_challenge_method: str = "S256"

    @staticmethod
    def generate() -> "PKCEChallenge":
        """Generate PKCE challenge and verifier."""
        code_verifier = secrets.token_urlsafe(32)
        code_sha = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = secrets.base64.urlsafe_b64encode(code_sha).decode().rstrip("=")
        return PKCEChallenge(
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )


@dataclass
class DeviceCodeResponse:
    """Device code authorization response."""
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: Optional[str]
    expires_in: int
    interval: int = 5
    message: Optional[str] = None

    def is_expired(self, issued_at: datetime) -> bool:
        """Check if device code has expired."""
        expiry = issued_at + timedelta(seconds=self.expires_in)
        return _utcnow() >= expiry


@dataclass
class Token:
    """OAuth token with metadata."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    issued_at: datetime = field(default_factory=_utcnow)

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token has expired."""
        expiry = self.issued_at + timedelta(seconds=self.expires_in)
        return _utcnow() >= (expiry - timedelta(seconds=buffer_seconds))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            "issued_at": self.issued_at.isoformat(),
        }
