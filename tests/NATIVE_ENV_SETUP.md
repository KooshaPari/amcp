# Native Environment Setup (No Docker Desktop Required)

## Philosophy

SmartCP tests use **native Python environments** and **lightweight services** where possible:
- ✅ Python virtual environments (venv/uv)
- ✅ Native service binaries (postgres, redis, neo4j) via Homebrew/system packages
- ✅ In-memory alternatives for testing
- ❌ Avoid Docker Desktop overhead
- ❌ Avoid heavy containerization for local dev

## Test Environment Requirements

### Minimal Setup (Unit Tests)
- ✅ Python 3.10+ virtual environment
- ✅ pytest + pytest-asyncio
- ✅ In-memory storage backends (no external services)

### Integration Tests (Optional)
- PostgreSQL: `brew install postgresql@16` or use in-memory SQLite
- Redis: `brew install redis` or use fakeredis
- Neo4j: Use in-memory graph or mock

## Native Service Alternatives

### Storage Backends
- **Memory**: `InMemoryStorage` (default for tests)
- **Redis**: Use `fakeredis` for testing
- **PostgreSQL**: Use SQLite in-memory for tests
- **Neo4j**: Mock or use in-memory graph

### Event Bus
- **NATS**: Use in-memory event bus for tests
- **Background Tasks**: Use asyncio tasks directly

## Test Configuration

Tests are designed to work **without external services**:
- All storage uses in-memory backends
- Event bus uses placeholder/mock implementations
- MCP servers use mock managers
- Skills use temporary file system

## Running Tests

```bash
# Unit tests (no services needed)
pytest tests/unit/ -v

# Component tests (no services needed)
pytest tests/component/ -v

# Integration tests (may need services, but use mocks by default)
pytest tests/integration/ -v

# Full suite (uses native Python only)
pytest tests/ -v
```

## Docker Usage

Docker configs (`docker-compose.yml`) are **optional** and only for:
- Full E2E testing with Bifrost stack
- Production-like environment testing
- CI/CD pipelines

**Not required** for:
- Unit tests ✅
- Component tests ✅
- Most integration tests ✅
- Local development ✅
