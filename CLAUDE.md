# AgentMCP — CLAUDE.md

## Project Summary

AgentMCP (SmartCP) is an MCP (Model Context Protocol) server with resource access enforcement. Provides tools, LLM integration, and multi-database support for AI agents.

## Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | FastAPI | 0.121 |
| MCP | fastmcp | 2.13 |
| DB | asyncpg, SQLAlchemy | 0.30, 2.0 |
| Cache | Redis | 5.0 |
| Graph DB | Neo4j | 6.0 |
| Vector DB | Qdrant | 1.16 |
| LLM | OpenAI, MLX | 1.0 |
| Auth | JWT, OAuth2 | - |

## Key Commands

```bash
# Install
pip install -e ".[dev]"

# Test
pytest
pytest --cov=. --cov-report=html

# Lint & Format
ruff check .
ruff format .

# Type check
pyright

# Run server
python server.py
python main.py serve
```

## Project Structure

```
AgentMCP/
├── server.py           # MCP server
├── main.py             # CLI entry
├── bifrost_client.py   # Bifrost integration
├── auth/               # Auth middleware
├── config/             # Settings
├── runtime/            # Agent runtime
│   ├── core.py
│   └── tools/
├── tools/              # Built-in tools
├── migrations/         # DB migrations
└── tests/              # Test suite
```

## Development Rules

- Use `asyncpg` for async PostgreSQL operations
- All API endpoints use FastAPI with Pydantic models
- Error handling with proper HTTP status codes
- Resource access enforcement in middleware
- Tool registration via decorator pattern

## Configuration

Environment variables in `.env`:
- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` — Redis connection
- `NEO4J_URI` — Neo4j connection
- `OPENAI_API_KEY` — OpenAI API key

## Quality Gates

- `pytest` — all tests pass
- `ruff check` — no lint errors
- `ruff format --check` — properly formatted
- `pyright` — no type errors
