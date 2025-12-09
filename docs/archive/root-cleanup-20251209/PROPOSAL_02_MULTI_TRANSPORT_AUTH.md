# Proposal 2: Multi-Transport Input Support with Flexible Auth

**ID:** PROPOSAL-002  
**Title:** Support Multiple Input Transports (stdio, SSE, HTTP) with Flexible Auth  
**Status:** DRAFT  
**Priority:** P0  
**Effort:** 35 story points  
**Timeline:** 2-3 weeks  
**Depends On:** Proposal 1 (FastMCP 2.13)

## Problem Statement

Current implementation primarily supports stdio transport. This limits:
- Web-based agent integration (requires HTTP/SSE)
- Browser-based tool execution
- Real-time streaming responses
- Flexible authentication schemes
- Multi-client concurrent access

## Solution Overview

Implement unified transport abstraction supporting:
1. **Stdio** - Local process communication (existing)
2. **SSE** - Server-Sent Events for streaming
3. **HTTP** - RESTful API with JSON-RPC
4. **Auth Providers** - OAuth, Bearer, Env, None, Custom

## Transport Architecture

### Unified Transport Interface
```python
class MCPTransport(Protocol):
    async def send(message: JSONRPCMessage) -> None
    async def receive() -> JSONRPCMessage
    async def close() -> None
    
class TransportFactory:
    def create_transport(config: TransportConfig) -> MCPTransport
```

### Supported Transports

#### 1. Stdio (Existing)
- Process stdin/stdout
- Local agent communication
- No network overhead

#### 2. SSE (Server-Sent Events)
- Unidirectional server→client streaming
- Browser-compatible
- Auto-reconnect support
- Heartbeat mechanism

#### 3. HTTP (JSON-RPC over HTTP)
- Bidirectional request/response
- RESTful endpoints
- WebSocket upgrade support
- CORS handling

## Authentication Providers

### 1. OAuth 2.0
```python
class OAuthProvider:
    async def authenticate(request: Request) -> AuthContext
    async def validate_token(token: str) -> bool
    async def refresh_token(token: str) -> str
```

### 2. Bearer Token
```python
class BearerTokenProvider:
    async def validate(token: str) -> bool
    def extract_from_header(header: str) -> str
```

### 3. Environment Variables
```python
class EnvVarProvider:
    def validate(env_key: str) -> bool
    def get_credentials() -> Credentials
```

### 4. None (Public)
```python
class NoAuthProvider:
    async def authenticate(request: Request) -> AuthContext
```

### 5. Custom
```python
class CustomAuthProvider:
    async def authenticate(request: Request) -> AuthContext
```

## Implementation Phases

### Phase 1: Transport Abstraction (Week 1)
- [ ] Define transport interface
- [ ] Implement stdio transport
- [ ] Create transport factory
- [ ] Add transport configuration

### Phase 2: HTTP & SSE (Week 2)
- [ ] Implement HTTP transport
- [ ] Implement SSE transport
- [ ] Add WebSocket support
- [ ] CORS middleware

### Phase 3: Auth Integration (Week 2-3)
- [ ] OAuth provider
- [ ] Bearer token provider
- [ ] Env var provider
- [ ] Custom provider support
- [ ] Auth middleware

## Configuration Example

```yaml
transports:
  stdio:
    enabled: true
  http:
    enabled: true
    host: 0.0.0.0
    port: 8000
    cors:
      allow_origins: ["*"]
  sse:
    enabled: true
    heartbeat_interval: 30s

auth:
  provider: oauth
  oauth:
    domain: auth.example.com
    client_id: ${OAUTH_CLIENT_ID}
    client_secret: ${OAUTH_CLIENT_SECRET}
```

## Testing Strategy

- Unit tests for each transport
- Integration tests for auth flows
- E2E tests for multi-transport scenarios
- Load tests for concurrent connections

## Success Criteria

- [ ] All 3 transports functional
- [ ] All 5 auth providers working
- [ ] Seamless transport switching
- [ ] Zero message loss
- [ ] <100ms latency overhead
- [ ] Full test coverage

## Related Proposals

- Proposal 1: FastMCP 2.13 (prerequisite)
- Proposal 3: Bash Environment (uses HTTP transport)
- Proposal 5: Tool Discovery (uses HTTP transport)

