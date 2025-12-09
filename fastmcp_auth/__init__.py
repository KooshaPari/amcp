"""
FastMCP Authentication Enhancement - DCR + PKCE Support

Extends FastMCP 2.13 authentication with:
- Device Code Request (DCR) flow for CLI/server-side applications
- PKCE (Proof Key for Code Exchange) for secure token exchange
- OAuth provider fallback mechanism with retry logic
- Secure token caching with TTL and encryption
- Automatic token refresh and rotation

This module provides production-grade authentication for MCP servers
supporting both interactive (DCR) and programmatic (PKCE) flows.
"""

from .models import OAuthFlow, PKCEChallenge, DeviceCodeResponse, Token
from .cache import TokenCache
from .providers import DCRProvider, PKCEProvider


__all__ = [
    "OAuthFlow",
    "PKCEChallenge",
    "DeviceCodeResponse",
    "Token",
    "TokenCache",
    "DCRProvider",
    "PKCEProvider",
]
