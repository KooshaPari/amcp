# SmartCP Middleware

Cross-cutting concerns for the SmartCP MCP server.

## Overview

This directory contains middleware modules that handle infrastructure concerns across all requests:

## Modules

### resource_access_enforcement.py (204 lines)

**Phase 5.1 Implementation: Bifrost Delegation Enforcement**

Enforces that all resource access in SmartCP goes through the Bifrost client, preventing direct database imports.

**Key Features:**
- Detects forbidden module imports (supabase, neo4j, redis, qdrant_client)
- Audit and strict enforcement modes
- Structured logging of violations
- Static validation helper for testing
- Defense-in-depth: runtime + linting rules

**Forbidden Modules:**
```
supabase, neo4j, redis, qdrant_client
```

These can only be imported in bifrost-extensions, not in smartcp.

**Approved Client:**
```
services.bifrost.bifrost_client
```

All resource access must use this abstraction.

**Usage in server.py:**
```python
# Audit mode (default, logs violations but allows requests)
app.add_middleware(
    ResourceAccessEnforcementMiddleware,
    enforce=False,
    log_violations=True,
)

# Strict mode (rejects requests with violations)
app.add_middleware(
    ResourceAccessEnforcementMiddleware,
    enforce=True,
    log_violations=True,
)
```

**Testing:**
```bash
pytest tests/unit/middleware/test_resource_access_enforcement.py -v
```

## Architecture

### Middleware Order

Middleware is processed in **reverse registration order** (outer to inner):

1. **ResourceAccessEnforcementMiddleware** (inner) - Resource access validation
2. **AuthMiddleware** (outer) - Bearer token validation

This defense-in-depth approach ensures resource enforcement happens before auth.

## Compliance

- **Phase 5.1 Remediation:** Complete
- **Architecture:** Stateless, Bifrost-delegated
- **File Size:** 214 total lines (< 350 target)
- **Test Coverage:** 16 tests, 100% coverage

## Future Middleware

This directory will contain additional middleware for:
- Rate limiting enforcement
- Request/response transformation
- Observability (tracing, metrics)
- Error handling and recovery

## References

- [REMEDIATION_SPECIFICATIONS.md](../REMEDIATION_SPECIFICATIONS.md) - Phase 5.1
- [PHASE_5_1_IMPLEMENTATION.md](../PHASE_5_1_IMPLEMENTATION.md) - Implementation details
- [tests/unit/middleware/](../tests/unit/middleware/) - Comprehensive test suite
