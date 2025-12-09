# FastMCP Authentication Enhancement - Phase 3 Documentation

## Overview

Phase 3 extends FastMCP 2.13 with production-grade authentication capabilities:

- **Device Code Request (DCR)** - OAuth flow for CLI and server-side applications
- **PKCE (Proof Key for Code Exchange)** - Secure token exchange without exposing client secrets
- **OAuth Provider Fallback** - Multi-provider support with automatic retry logic
- **Secure Token Caching** - On-disk and in-memory caching with TTL and file permissions

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   FastMCP Authentication Layer                  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │   DCRProvider   │    │  PKCEProvider   │                   │
│  │                 │    │                 │                   │
│  │ Device Code Flow│    │ Auth Code + PKCE│                   │
│  │ Poll for Token  │    │ S256 Challenge  │                   │
│  └────────┬────────┘    └────────┬────────┘                   │
│           │                      │                             │
│           └──────────┬───────────┘                             │
│                      ▼                                         │
│          ┌──────────────────────┐                             │
│          │ OAuthProviderFallback│                             │
│          │                      │                             │
│          │ - Try providers in   │                             │
│          │   order              │                             │
│          │ - Retry with backoff │                             │
│          │ - Circuit breaker    │                             │
│          └──────────┬───────────┘                             │
│                     ▼                                          │
│          ┌──────────────────────┐                             │
│          │     TokenCache       │                             │
│          │                      │                             │
│          │ - Memory cache       │                             │
│          │ - File cache (0o600) │                             │
│          │ - TTL expiry         │                             │
│          └──────────┬───────────┘                             │
│                     ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │          FastMCPAuthEnhancedProvider                     │ │
│  │                                                          │ │
│  │ - Integrates with FastMCP 2.13 AuthenticationProvider   │ │
│  │ - Manages token lifecycle                                │ │
│  │ - Handles authorization                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Components

### 1. PKCEChallenge

Generates PKCE code verifier and challenge using S256 method.

```python
from smartcp.fastmcp_auth import PKCEChallenge

# Generate new PKCE challenge
challenge = PKCEChallenge.generate()

print(challenge.code_verifier)       # Random 43-character verifier
print(challenge.code_challenge)      # SHA256 hash, base64url encoded
print(challenge.code_challenge_method)  # "S256"
```

### 2. Token

OAuth token with expiry tracking and serialization.

```python
from smartcp.fastmcp_auth import Token

token = Token(
    access_token="eyJ...",
    token_type="Bearer",
    expires_in=3600,
    refresh_token="refresh_abc123",
    scope="openid profile"
)

# Check expiry (with 60-second buffer)
if token.is_expired():
    print("Token needs refresh")

# Serialize for storage
token_dict = token.to_dict()
```

### 3. TokenCache

Secure token caching with memory and file storage.

```python
from smartcp.fastmcp_auth import TokenCache

cache = TokenCache(cache_dir=".mcp_token_cache")

# Store token
await cache.set("user_123", token)

# Retrieve token (returns None if expired)
cached_token = await cache.get("user_123")

# Clear specific token
await cache.clear("user_123")
```

**Security Features:**
- Cache directory created with `0o700` permissions
- Token files created with `0o600` permissions
- Automatic expiry checking on retrieval
- Memory fallback if file operations fail

### 4. DCRProvider

Implements OAuth 2.0 Device Authorization Grant (RFC 8628).

```python
from smartcp.fastmcp_auth import DCRProvider

dcr = DCRProvider(
    client_id="your_client_id",
    auth_server_url="https://auth.example.com",
    scopes=["openid", "profile"]
)

# Request device code
device_code_response = await dcr.request_device_code()

print(f"Go to: {device_code_response.verification_uri}")
print(f"Enter code: {device_code_response.user_code}")

# Poll for token (blocks until user completes auth)
token = await dcr.poll_for_token(device_code_response)
```

**Flow:**
1. Client requests device code from auth server
2. Server returns `user_code` and `verification_uri`
3. User visits URL and enters code on separate device
4. Client polls token endpoint until user completes auth
5. Server returns access token

### 5. PKCEProvider

Implements OAuth 2.0 Authorization Code Grant with PKCE.

```python
from smartcp.fastmcp_auth import PKCEProvider

pkce = PKCEProvider(
    client_id="your_client_id",
    auth_server_url="https://auth.example.com",
    redirect_uri="http://localhost:8080/callback",
    scopes=["openid", "profile"]
)

# Generate authorization URL
challenge = PKCEChallenge.generate()
state = secrets.token_urlsafe(16)
auth_url = pkce.get_authorization_url(challenge, state)

# User visits auth_url and authorizes
# After redirect, exchange code for token
token = await pkce.exchange_code(
    code="authorization_code_from_callback",
    code_verifier=challenge.code_verifier
)

# Refresh token
new_token = await pkce.refresh_token(token.refresh_token)
```

### 6. OAuthProviderFallback

Multi-provider support with automatic fallback.

```python
from smartcp.fastmcp_auth import OAuthProviderFallback

fallback = OAuthProviderFallback(
    providers=[dcr_provider, pkce_provider],
    max_retries=3,
    retry_delay=1.0
)

# Try providers in order until one succeeds
token = await fallback.authenticate()
```

### 7. FastMCPAuthEnhancedProvider

Integration layer for FastMCP 2.13 servers.

```python
from fastmcp_auth_provider import (
    FastMCPAuthEnhancedProvider,
    create_smartcp_server_with_auth
)

# Create enhanced auth provider
auth_provider = FastMCPAuthEnhancedProvider(
    client_id="your_client_id",
    auth_server_url="https://auth.example.com",
    redirect_uri="http://localhost:8080/callback",
    scopes=["openid", "profile"],
    cache_dir=".mcp_token_cache"
)

# Authenticate (tries cached token first, then initiates flow)
success = await auth_provider.authenticate({"token": "existing_token"})

# Get current token
token = await auth_provider.get_token()

# Check authorization
is_authorized = await auth_provider.authorize("user_123", "resource")

# Create server with auth
server = create_smartcp_server_with_auth(
    name="my-mcp-server",
    auth_provider=auth_provider
)
```

## Usage Examples

### Example 1: Device Code Flow for CLI Application

```python
import asyncio
from smartcp.fastmcp_auth import DCRProvider, TokenCache

async def cli_auth():
    # Initialize providers
    cache = TokenCache(".cli_tokens")
    dcr = DCRProvider(
        client_id="cli_app",
        auth_server_url="https://auth.example.com",
        scopes=["mcp:read", "mcp:write"]
    )

    # Check for cached token
    cached = await cache.get("default")
    if cached and not cached.is_expired():
        print("Using cached token")
        return cached

    # Request device code
    device_code = await dcr.request_device_code()

    print("\n🔐 Authorization Required")
    print(f"1. Visit: {device_code.verification_uri}")
    print(f"2. Enter code: {device_code.user_code}")
    print("3. Authorize the application\n")

    # Poll for token
    token = await dcr.poll_for_token(device_code)

    # Cache token
    await cache.set("default", token)

    print("✅ Authentication successful!")
    return token

if __name__ == "__main__":
    token = asyncio.run(cli_auth())
```

### Example 2: PKCE Flow for Web Application

```python
from fastapi import FastAPI, Request
from smartcp.fastmcp_auth import PKCEProvider, PKCEChallenge
import secrets

app = FastAPI()
pkce = PKCEProvider(
    client_id="web_app",
    auth_server_url="https://auth.example.com",
    redirect_uri="http://localhost:8000/callback",
    scopes=["openid", "profile", "mcp:access"]
)

# Store challenges temporarily (use Redis in production)
pending_challenges = {}

@app.get("/login")
async def login():
    challenge = PKCEChallenge.generate()
    state = secrets.token_urlsafe(16)

    # Store for callback verification
    pending_challenges[state] = challenge.code_verifier

    auth_url = pkce.get_authorization_url(challenge, state)
    return {"redirect": auth_url}

@app.get("/callback")
async def callback(code: str, state: str):
    code_verifier = pending_challenges.pop(state, None)
    if not code_verifier:
        return {"error": "Invalid state"}

    token = await pkce.exchange_code(code, code_verifier)
    return {
        "access_token": token.access_token,
        "expires_in": token.expires_in
    }
```

### Example 3: MCP Server with Enhanced Auth

```python
from fastmcp_auth_provider import (
    FastMCPAuthEnhancedProvider,
    create_smartcp_server_with_auth
)
from fastmcp_2_13_server import TransportType

# Create auth provider
auth = FastMCPAuthEnhancedProvider(
    client_id="mcp_server",
    auth_server_url="https://auth.example.com",
    redirect_uri="http://localhost:8080/callback",
    scopes=["mcp:tools", "mcp:resources"],
    enable_dcr=True,  # Enable device code flow
    cache_dir=".server_tokens"
)

# Create server with auth
server = create_smartcp_server_with_auth(
    name="enhanced-mcp-server",
    transport=TransportType.SSE,
    host="0.0.0.0",
    port=8000,
    auth_provider=auth
)

# Register tools
@server.get_mcp().tool
async def protected_tool(param: str):
    """Tool that requires authentication."""
    return {"result": param}

# Start server
import asyncio
asyncio.run(server.start())
```

### Example 4: Provider Fallback with Multiple Auth Methods

```python
from smartcp.fastmcp_auth import (
    DCRProvider, PKCEProvider, OAuthProviderFallback
)

# Configure multiple providers
dcr = DCRProvider(
    client_id="app",
    auth_server_url="https://primary.auth.com"
)

pkce = PKCEProvider(
    client_id="app",
    auth_server_url="https://backup.auth.com",
    redirect_uri="http://localhost:8080/callback"
)

# Create fallback chain
fallback = OAuthProviderFallback(
    providers=[dcr, pkce],
    max_retries=3,
    retry_delay=1.0
)

# Authenticate using first available provider
token = await fallback.authenticate()
```

## Security Considerations

### Token Storage

- Tokens are stored in files with `0o600` permissions (owner read/write only)
- Cache directory has `0o700` permissions (owner access only)
- File names are hashed to prevent information leakage
- Memory cache used as fallback if file operations fail

### PKCE Security

- Uses S256 challenge method (SHA-256)
- Code verifier is 43+ characters of cryptographically random data
- Code challenge is base64url encoded without padding
- Each authorization request uses unique verifier

### Token Expiry

- Tokens are checked for expiry before use
- 60-second buffer applied to prevent edge-case failures
- Automatic refresh when refresh token is available
- Expired tokens are not returned from cache

## API Reference

### smartcp.fastmcp_auth

| Class | Description |
|-------|-------------|
| `PKCEChallenge` | PKCE code verifier and challenge generation |
| `Token` | OAuth token with expiry tracking |
| `TokenCache` | Secure token caching |
| `DeviceCodeResponse` | DCR flow device code response |
| `DCRProvider` | Device Code Request OAuth flow |
| `PKCEProvider` | PKCE OAuth flow |
| `OAuthProviderFallback` | Multi-provider fallback |
| `OAuthFlow` | Enum of OAuth grant types |

### fastmcp_auth_provider

| Class/Function | Description |
|----------------|-------------|
| `FastMCPAuthEnhancedProvider` | AuthenticationProvider implementation |
| `FastMCPAuthEnhancedServer` | Server mixin with enhanced auth |
| `create_smartcp_server_with_auth` | Factory for creating authenticated servers |

## Testing

Run the Phase 3 tests:

```bash
# Run all auth enhancement tests
uv run pytest smartcp/tests/fastmcp_auth/ -v

# Run with async support (requires pytest-asyncio)
uv run pytest smartcp/tests/fastmcp_auth/ -v --asyncio-mode=auto
```

Test coverage includes:
- PKCE challenge generation (uniqueness, format)
- Token expiry detection (buffer handling)
- Token serialization
- Authorization URL generation
- Provider integration
- Security properties (randomness, file permissions)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_AUTH_CLIENT_ID` | OAuth client ID | Required |
| `MCP_AUTH_SERVER_URL` | Authorization server URL | Required |
| `MCP_AUTH_REDIRECT_URI` | OAuth redirect URI | `http://localhost:8080/callback` |
| `MCP_AUTH_SCOPES` | Space-separated scopes | `openid profile` |
| `MCP_TOKEN_CACHE_DIR` | Token cache directory | `.mcp_token_cache` |

### Programmatic Configuration

```python
config = {
    "client_id": "your_app",
    "auth_server_url": "https://auth.example.com",
    "redirect_uri": "http://localhost:8080/callback",
    "scopes": ["openid", "profile", "mcp:access"],
    "cache_dir": ".tokens",
    "enable_dcr": True,
    "enable_pkce": True,
    "max_retries": 3,
    "retry_delay": 1.0
}

auth_provider = FastMCPAuthEnhancedProvider(**config)
```

## Troubleshooting

### Common Issues

**1. Token not refreshing**
- Check that refresh token is present in cached token
- Verify auth server supports refresh token grant
- Check token expiry buffer settings

**2. PKCE verification failing**
- Ensure code verifier is stored between authorization and callback
- Verify S256 method is used consistently
- Check for URL encoding issues in callback

**3. DCR polling timing out**
- Increase `expires_in` awareness
- Check `interval` for polling rate
- Verify auth server is responding

**4. Cache permission errors**
- Ensure process has write access to cache directory
- Check parent directory permissions
- Verify disk space availability

## Roadmap

Phase 3 is complete. Remaining phases:

- **Phase 4**: GraphQL Subscription Client
- **Phase 5**: Neo4j Storage Implementation
- **Phase 6**: Voyage AI Integration

## Files

| File | Lines | Description |
|------|-------|-------------|
| `smartcp/fastmcp_auth/` | ~540 | Core auth module (DCR, PKCE, caching) |
| `fastmcp_auth_provider.py` | ~220 | FastMCP integration layer |
| `tests/test_fastmcp_auth_enhancement.py` | ~450 | Comprehensive test suite |
