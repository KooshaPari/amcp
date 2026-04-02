<!-- Last synced: 2026-04-02 -->

# AGENTS.md — AgentMCP

## Project Identity

- **Name**: AgentMCP (SmartCP)
- **Description**: MCP Server with resource access enforcement
- **Location**: `/Users/kooshapari/CodeProjects/Phenotype/repos/AgentMCP`
- **Language Stack**: Python 3.10+
- **Package Manager**: uv

## AgilePlus Integration

All work MUST be tracked in AgilePlus:
- Reference: `/Users/kooshapari/CodeProjects/Phenotype/repos/.agileplus`
- CLI: `agileplus <command>`
- No code without corresponding AgilePlus spec

---

## Repository Mental Model

### Project Structure

```
AgentMCP/
├── server.py              # MCP server entry
├── main.py                # CLI entry point
├── bifrost_client.py      # Bifrost integration
├── auth/                  # Authentication & middleware
│   ├── token.py          # JWT token handling
│   └── middleware.py      # Auth middleware
├── config/                # Configuration management
│   └── settings.py       # Pydantic settings
├── runtime/               # Agent runtime
│   ├── core.py           # Core runtime logic
│   └── tools/
│       ├── registry.py    # Tool registry
│       ├── discovery.py   # Tool discovery
│       ├── decorator.py   # Tool decorators
│       └── types.py      # Tool types
├── tools/                 # Built-in tools
│   └── execute.py
├── migrations/            # Database migrations
└── tests/                 # Test suite
    ├── unit/
    ├── integration/
    └── e2e/
```

### Style Constraints

- **Formatter**: `ruff format` (mandatory)
- **Linter**: `ruff check` (zero errors)
- **Type Checker**: `pyright` (strict mode)
- **Line length**: 100 characters
- **Type annotations**: Required for all public APIs

### Key Constraints

- Use `asyncpg` for async PostgreSQL
- All endpoints use Pydantic models for request/response
- Error handling via HTTPException with proper status codes
- Tool registration via `@tool` decorator
- Resource access enforced via middleware

---

## Key Commands

```bash
# Install
uv pip install -e ".[dev]"

# Test
pytest
pytest --cov=. --cov-report=html

# Lint & Format
ruff check .
ruff format .

# Type check
pyright

# Run
python server.py
python main.py serve
```

---

## Quality Gates

- `pytest` — all tests pass
- `ruff check` — zero lint errors
- `ruff format --check` — properly formatted
- `pyright` — zero type errors
