# AgentMCP (SmartCP)

MCP Server with resource access enforcement for AI agents. Provides tools and capabilities for agent runtime with multi-database support.

## Overview

SmartCP is an MCP (Model Context Protocol) server that provides:
- **Resource Access Enforcement**: Secure resource access control
- **Multi-Database Support**: PostgreSQL, Neo4j, Redis, Qdrant, Supabase
- **LLM Integration**: OpenAI, MLX, Transformers
- **Tool Discovery & Registry**: Dynamic tool registration and execution
- **Bifrost Extension**: Phenotype-specific extensions

## Installation

```bash
# From source
pip install -e .

# With dev dependencies
pip install -e ".[dev]"

# Using uv
uv pip install -e .
```

## Quick Start

```bash
# Run the MCP server
python server.py

# Or use the CLI
python main.py serve
```

## Configuration

Set environment variables or create `.env`:

```bash
DATABASE_URL=postgresql://localhost:5432/smartcp
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
OPENAI_API_KEY=sk-...
```

## Architecture

```
AgentMCP/
├── server.py              # MCP server entry
├── main.py                # CLI entry point
├── bifrost_client.py      # Bifrost integration
├── auth/                  # Authentication & middleware
├── config/                # Configuration management
├── runtime/               # Agent runtime
│   ├── core.py           # Core runtime logic
│   ├── tools/            # Tool system
│   └── mcp/              # MCP protocol
├── tools/                 # Built-in tools
├── migrations/            # Database migrations
└── tests/                 # Test suite
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Lint
ruff check .

# Format
ruff format .

# Type check
pyright
```

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest --config=pytest.e2e.ini tests/e2e/
```

## License

MIT OR Apache-2.0
