# SmartCP Documentation

SmartCP is an advanced MCP (Model Context Protocol) aggregator with intelligent routing, multi-transport support, and comprehensive tool management.

**Version:** 0.1.0
**Last Updated:** December 2025 (Phase 0.5 Complete)

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Architecture](ARCHITECTURE.md) | System architecture, layer hierarchy, and design patterns |
| [Modules](MODULES.md) | Module structure and import migration guide |
| [Architecture Details](architecture/) | In-depth architecture documentation |
| [Implementation](implementation/) | Implementation guides and proposals |
| [Deployment](deployment/) | Deployment guides and configuration |
| [Migration](migration/) | Migration guides and consolidation |
| [Testing](testing/) | Testing and validation |
| [SDK](sdk/) | SDK documentation |
| [Reference](reference/) | Reference materials and research |
| [Sessions](sessions/) | Session-based work documentation |

---

## Module Structure (Phase 0.5)

After the Phase 0.5 reorganization, the SmartCP codebase follows a clean layered architecture:

```
smartcp/
|
|-- agents/                    # Agent Framework Layer
|   |-- dsl_scope/            # DSL scope system (11-level hierarchy)
|   |   |-- inference/        # Scope inference engine
|   |   |-- ...
|   |-- ...
|
|-- auth/                      # Authentication Layer
|   |-- middleware.py         # Auth middleware
|   |-- token.py              # Token validation
|   |-- context.py            # User context management
|   |-- provider.py           # FastMCP auth provider
|   |-- session_manager.py    # Session management
|   |-- ...
|
|-- bifrost/                   # Bifrost Subsystem
|   |-- control_plane.py      # Control plane logic
|
|-- bifrost_api/              # HTTP API Layer
|   |-- routes.py             # API routes
|   |-- schemas.py            # Request/response schemas
|   |-- middleware/           # API middleware
|   |-- ...
|
|-- bifrost_extensions/       # Extension Framework
|   |-- analysis/             # Analysis extensions
|   |-- client/               # Client extensions
|   |-- config/               # Configuration extensions
|   |-- observability/        # Observability extensions
|   |-- providers/            # Provider extensions
|   |-- resilience/           # Resilience extensions
|   |-- routing/              # Routing extensions
|   |-- security/             # Security extensions
|   |-- ...
|
|-- bifrost_ml/               # ML Integration
|   |-- services/             # ML services
|   |-- proto/                # Protocol definitions
|   |-- ...
|
|-- infrastructure/           # Infrastructure Layer
|   |-- adapters/             # External service adapters
|   |   |-- neo4j/           # Neo4j adapter (moved from root)
|   |   |-- vector_db.py     # Vector database adapter
|   |-- bifrost/              # Bifrost infrastructure
|   |-- common/               # Common utilities
|   |-- executors/            # Code executors
|   |-- state/                # State management
|   |-- ...
|
|-- mcp/                       # MCP Integration Layer
|   |-- registry.py           # MCP registry
|   |-- discovery.py          # Server discovery
|   |-- builder.py            # Custom builders
|   |-- loaders.py            # Lazy loading
|   |-- lifecycle.py          # Lifecycle management
|   |-- reloader.py           # Hot reload
|   |-- security.py           # Security sandbox
|   |-- inference.py          # Inference bridge
|   |-- tools/                # Tool submodule
|   |-- ...
|
|-- middleware/               # Global Middleware
|   |-- ...
|
|-- models/                    # Data Models Layer
|   |-- schemas.py            # Pydantic schemas
|   |-- bifrost.py            # Bifrost models
|   |-- ...
|
|-- optimization/             # Optimization Layer
|   |-- compression/          # Context compression
|   |-- memory/               # Memory optimization
|   |-- model_router/         # Model routing
|   |-- parallel_executor/    # Parallel execution
|   |-- planning/             # Planning strategies
|   |-- ...
|
|-- services/                  # Business Logic Layer
|   |-- bifrost/              # Bifrost services
|   |-- vibeproxy/            # Vibeproxy services
|   |-- memory.py             # Memory service
|   |-- executor.py           # Executor service
|   |-- ...
|
|-- tools/                     # MCP Tools Layer
|   |-- execute.py            # Execute tool
|   |-- memory.py             # Memory tools
|   |-- state.py              # State tools
|   |-- analysis/             # Analysis tools
|   |-- ...
|
|-- config/                    # Configuration
|-- migrations/               # Database migrations
|-- tests/                     # Test suite
|-- docs/                      # Documentation
|
|-- server.py                  # MCP server entrypoint
|-- main.py                    # Application entrypoint
|-- conftest.py               # Test configuration
```

---

## Key Components

### Authentication (`auth/`)

Bearer token authentication with JWT validation and user-scoped context:

```python
from auth import (
    AuthMiddleware,
    TokenValidator,
    JWTConfig,
    UserContextProvider,
    FastMCPAuthEnhancedProvider,
)
```

### Agent DSL Scope (`agents/dsl_scope/`)

11-level scope hierarchy for the Python DSL:

```python
from agents.dsl_scope import (
    ScopeLevel,
    DSLScopeSystem,
    ComprehensiveScopeInferenceEngine,
    InferenceSignal,
)
```

### MCP Integration (`mcp/`)

Complete MCP protocol integration:

```python
from mcp import tools
from mcp.registry import MCPRegistry
from mcp.inference import MCPInferenceBridge
```

### Services (`services/`)

Business logic services:

```python
from services import (
    UserScopedMemory,
    UserScopedExecutor,
    create_memory_service,
    create_executor_service,
)
```

### Infrastructure (`infrastructure/`)

External adapters and common utilities:

```python
from infrastructure import adapters, executors, common, bifrost
from infrastructure.adapters.neo4j import Neo4jAdapter
```

### Optimization (`optimization/`)

2025-grade optimizations for agentic AI:

```python
from optimization import (
    PromptCache,
    ComplexityRouter,
    ReAcTreePlanner,
    ParallelToolExecutor,
    ACONCompressor,
)
```

---

## Documentation Sections

### Architecture

- [Architecture Overview](ARCHITECTURE.md) - System architecture and design
- [Architecture Details](architecture/) - In-depth architecture documentation

### Implementation

- [Implementation Guides](implementation/) - Implementation guides
- [Proposals](implementation/) - Feature proposals
- [Executors](implementation/) - Executor implementations
- [Router](implementation/) - Router implementations

### Deployment

- [Deployment Guides](deployment/) - Deployment guides
- [Local Deployment](../LOCAL_DEPLOYMENT.md) - Local development setup

### Migration

- [Module Migration](MODULES.md) - Import path migration guide
- [Migration Guides](migration/) - General migration guides

### Testing

- [Testing Guides](testing/) - Testing guides
- [Code Coverage Guide](CODE_COVERAGE_GUIDE.md) - Coverage requirements

### SDK

- [Bifrost SDK](sdk/bifrost/) - Bifrost SDK documentation
- [SmartCP SDK](sdk/smartcp/) - SmartCP SDK documentation
- [OpenAPI](sdk/openapi/) - OpenAPI specifications

### Reference

- [Research](reference/) - Research documents
- [Analysis](reference/) - Analysis documents
- [Work Packages](work-packages/) - Phased work packages

### Sessions

- [Session Docs](sessions/) - Session-based work documentation

---

## Getting Started

### Prerequisites

- Python 3.10+
- uv package manager (recommended)
- Virtual environment

### Quick Start

```bash
# Activate environment
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Run tests
python cli.py test run --scope unit

# Start server
python cli.py server start
```

### Import Examples

```python
# Authentication
from auth import AuthMiddleware, get_current_user_context

# Services
from services import UserScopedMemory, UserScopedExecutor

# Models
from models import UserContext, ExecuteCodeRequest

# Tools
from tools import register_execute_tool, register_memory_tools

# MCP Integration
from mcp.inference import MCPInferenceBridge

# Agent DSL
from agents.dsl_scope import DSLScopeSystem, ScopeLevel

# Optimization
from optimization import PromptCache, ComplexityRouter

# Infrastructure
from infrastructure.adapters.neo4j import adapter as neo4j_adapter
```

---

## Support

For issues and questions:
- Check the [Architecture Documentation](ARCHITECTURE.md)
- Review the [Module Migration Guide](MODULES.md)
- See session documentation in [sessions/](sessions/)
- Consult the main [CLAUDE.md](../CLAUDE.md) for development guidelines
