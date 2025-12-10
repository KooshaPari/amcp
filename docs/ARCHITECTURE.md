# SmartCP Architecture

## Overview

SmartCP consists of two main components:

1. **`server.py`** - MCP Server (FastMCP protocol)
2. **`main.py`** - FastAPI HTTP API (REST endpoints)

Both components delegate to Bifrost backend via `bifrost_client.py`.

## Components

### MCP Server (`server.py`)
- **Protocol**: FastMCP 2.13 (stateless HTTP)
- **Purpose**: MCP protocol frontend
- **Entry Point**: `SmartCPServer.create()`
- **Tools**: Single `execute` tool that uses AgentRuntime

### HTTP API (`main.py`)
- **Framework**: FastAPI
- **Purpose**: REST API endpoints for tool routing, search, etc.
- **Entry Point**: `app` (FastAPI application)
- **Endpoints**: `/health`, `/route`, `/tools`, `/semantic-search`

### Bifrost Client (`bifrost_client.py`)
- **Purpose**: GraphQL client for Bifrost backend delegation
- **Used By**: Both `server.py` and `main.py`
- **Default URL**: `http://localhost:8080/graphql`

## Go CLI (`cmd/smartcpcli/`)

The Go CLI (`smartcpcli`) is a separate tool for:
- Building and deploying SmartCP
- Managing services
- Health checks and logs

**Note**: Go code is excluded from Python coverage metrics.
