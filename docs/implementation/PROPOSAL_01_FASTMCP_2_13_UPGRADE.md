# PROPOSAL 01: FastMCP 2.13 Upgrade & Composition Patterns

**Status:** PROPOSED  
**Priority:** P0 (Critical)  
**Effort:** 3 weeks  
**Dependencies:** None

## Problem Statement

The python-proto-ref implementation uses a monolithic architecture that doesn't leverage FastMCP 2.13's advanced composition and proxy patterns. This limits:
- Server composition (local + remote)
- Proxy capabilities for arbitrary MCP servers
- Type-safe tool composition
- Middleware patterns

## Solution Overview

Upgrade to FastMCP 2.13 and implement:
1. **Server Composition** - Combine multiple MCP servers
2. **Proxy Patterns** - Wrap and extend existing servers
3. **Middleware Stack** - Auth, logging, rate limiting
4. **Type-Safe Tools** - Pydantic-based tool definitions

## Architecture

```
┌─────────────────────────────────────────┐
│         FastMCP 2.13 Server             │
├─────────────────────────────────────────┤
│  Middleware Stack                       │
│  ├─ Auth Middleware                     │
│  ├─ Logging Middleware                  │
│  ├─ Rate Limiting Middleware            │
│  └─ Error Handling Middleware           │
├─────────────────────────────────────────┤
│  Composition Layer                      │
│  ├─ Local Tool Registry                 │
│  ├─ Remote Server Proxies               │
│  ├─ Tool Aggregation                    │
│  └─ Conflict Resolution                 │
├─────────────────────────────────────────┤
│  Transport Layer                        │
│  ├─ stdio (primary)                     │
│  ├─ SSE (secondary)                     │
│  └─ HTTP (tertiary)                     │
└─────────────────────────────────────────┘
```

## Key Components

### 1. Composition Manager
```python
class CompositionManager:
    """Manages local and remote server composition"""
    
    def add_local_server(self, name: str, server: MCPServer)
    def add_remote_server(self, name: str, config: RemoteConfig)
    def proxy_server(self, name: str, config: ProxyConfig)
    def resolve_conflicts(self, tool_name: str) -> Tool
    def list_all_tools(self) -> List[Tool]
```

### 2. Proxy Pattern
```python
class ServerProxy:
    """Proxies calls to remote MCP servers"""
    
    async def call_tool(self, tool_name: str, args: dict) -> Any
    async def list_tools(self) -> List[Tool]
    async def get_tool_schema(self, tool_name: str) -> dict
```

### 3. Middleware Stack
```python
class MiddlewareStack:
    """Composable middleware for request/response handling"""
    
    def add_middleware(self, middleware: Middleware)
    async def process_request(self, request: Request) -> Request
    async def process_response(self, response: Response) -> Response
```

## Implementation Plan

### Phase 1: Core Upgrade (Week 1)
- [ ] Update FastMCP to 2.13
- [ ] Implement CompositionManager
- [ ] Add basic middleware support
- [ ] Write unit tests

### Phase 2: Proxy Patterns (Week 2)
- [ ] Implement ServerProxy
- [ ] Add remote server support
- [ ] Implement conflict resolution
- [ ] Integration tests

### Phase 3: Advanced Features (Week 3)
- [ ] Tool aggregation
- [ ] Dynamic composition
- [ ] Performance optimization
- [ ] Documentation

## Benefits

✅ Cleaner architecture  
✅ Better code reuse  
✅ Easier testing  
✅ Type safety  
✅ Middleware extensibility  

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Breaking changes | Comprehensive test suite |
| Performance impact | Benchmarking & optimization |
| Complexity | Clear documentation |

## Success Criteria

- [ ] All tests passing
- [ ] Composition working with 3+ servers
- [ ] Middleware stack functional
- [ ] Performance within 5% of baseline
- [ ] Documentation complete

---

**Next:** PROPOSAL_02 (Multi-Transport & Auth)

