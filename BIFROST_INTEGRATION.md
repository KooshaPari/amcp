# Bifrost Integration - SmartCP to Bifrost Backend

## Overview

SmartCP now properly delegates to Bifrost backend via GraphQL. SmartCP handles MCP protocol, while Bifrost handles all business logic (routing, tool execution, search).

## Architecture

```
┌─────────────┐         GraphQL          ┌──────────────┐
│   SmartCP   │◄─────────────────────────►│   Bifrost    │
│  (MCP API)  │    queries/mutations/     │  (Backend)   │
│             │      subscriptions        │              │
└─────────────┘                           └──────────────┘
      │                                          │
      │                                          │
      ▼                                          ▼
  MCP Protocol                            Business Logic
  Handling Only                         Routing, Tools, Search
```

## BifrostClient

### Implementation

`bifrost_client.py` extends `GraphQLSubscriptionClient` with:

**Core Methods:**
- `query()` - Execute GraphQL queries
- `mutate()` - Execute GraphQL mutations
- `subscribe()` - Subscribe to real-time events (inherited)

**High-Level API:**
- `query_tools()` - Get available tools
- `query_tool(name)` - Get tool metadata
- `route_request(prompt, context)` - Get routing decision
- `execute_tool(name, input)` - Execute tool via Bifrost
- `semantic_search(query, options)` - Search via Bifrost
- `register_tool()` - Register new tool
- `subscribe_tool_events()` - Monitor tool execution
- `subscribe_routing_events()` - Monitor routing decisions

### GraphQL Schema

```graphql
# Tool queries
query Tools($filters: ToolFilters, $limit: Int)
query Tool($name: String!)
query RouteRequest($prompt: String!, $context: JSON)
query SemanticSearch($query: String!, $limit: Int, $filters: JSON)

# Tool mutations
mutation ExecuteTool($name: String!, $input: JSON!)
mutation RegisterTool($tool: ToolInput!)

# Subscriptions
subscription ToolEvents($toolName: String!, $workspaceId: ID)
subscription RoutingEvents($workspaceId: ID)
```

## SmartCP API Changes

### Before (Direct Business Logic)

```python
# SmartCP contained routing logic
@app.post("/route")
async def route_query(request: RoutingRequest):
    # Local routing logic
    discovery_result = await pre_discovery_hook(...)
    return RoutingResponse(...)

# SmartCP contained search logic
@app.post("/search/semantic")
async def semantic_search(query: str):
    # Local embedding + search
    embedding = embedding_manager.generate_embedding(query)
    results = await search_service.semantic_search(...)
    return results
```

### After (Delegation to Bifrost)

```python
# SmartCP delegates to Bifrost
@app.post("/route")
async def route_query(request: RoutingRequest):
    # Delegate to Bifrost
    decision = await bifrost_client.route_request(
        prompt=request.prompt,
        context=request.context
    )
    return RoutingResponse(...)

# SmartCP delegates search to Bifrost
@app.post("/search/semantic")
async def semantic_search(query: str):
    # Delegate to Bifrost
    results = await bifrost_client.semantic_search(
        query=query,
        limit=limit
    )
    return results
```

## Usage Examples

### Basic Usage

```python
from bifrost_client import BifrostClient

# Initialize client
async with BifrostClient() as client:
    # Query available tools
    tools = await client.query_tools()

    # Route request
    decision = await client.route_request(
        prompt="Create a new project",
        context={"workspace_id": "123"}
    )

    # Execute tool
    result = await client.execute_tool(
        name=decision.selected_tool,
        input_data={"name": "Project", "description": "Test"}
    )
```

### With Environment Variables

```bash
export BIFROST_URL="ws://localhost:4000/graphql"
export BIFROST_API_KEY="your_api_key"
```

```python
# Client automatically reads from environment
client = BifrostClient()
```

### Subscriptions

```python
async def handle_tool_event(event):
    print(f"Tool executed: {event['data']['toolExecuted']}")

# Subscribe to tool events
sub_id = await client.subscribe_tool_events(
    tool_name="entity_create",
    handler=handle_tool_event
)

# Later: unsubscribe
await client.unsubscribe(sub_id)
```

## Testing

### Unit Tests

```bash
# Run BifrostClient unit tests
pytest tests/test_bifrost_client.py -v

# Run with coverage
pytest tests/test_bifrost_client.py --cov=bifrost_client
```

### Integration Tests

```bash
# Run SmartCP → Bifrost integration tests
pytest tests/test_bifrost_integration.py -v

# Test specific workflow
pytest tests/test_bifrost_integration.py::TestEndToEndWorkflow -v
```

### Mock Bifrost Server (for testing)

```python
# tests/mock_bifrost_server.py
from unittest.mock import AsyncMock

def create_mock_bifrost():
    """Create mock Bifrost server for testing."""
    client = AsyncMock(spec=BifrostClient)

    # Mock query_tools
    client.query_tools = AsyncMock(return_value=[
        ToolMetadata(name="entity_create", ...)
    ])

    # Mock route_request
    client.route_request = AsyncMock(return_value=RoutingDecision(
        selected_tool="entity_create",
        confidence=0.95,
        ...
    ))

    return client
```

## Error Handling

### Connection Errors

```python
try:
    await client.connect()
except ConnectionError as e:
    logger.error(f"Cannot connect to Bifrost: {e}")
    # Fallback to local mode or raise
```

### GraphQL Errors

```python
try:
    result = await client.query(...)
except ValueError as e:
    # GraphQL errors (validation, not found, etc.)
    logger.error(f"GraphQL error: {e}")
```

### Timeout Errors

```python
try:
    decision = await client.route_request(...)
except asyncio.TimeoutError:
    logger.error("Bifrost request timed out")
```

## Configuration

### BifrostClient Config

```python
client = BifrostClient(
    url="ws://localhost:4000/graphql",  # Bifrost GraphQL URL
    api_key="your_key",                 # Optional API key
    timeout=30.0,                       # Request timeout (seconds)
    connection_timeout=30.0,            # WebSocket connection timeout
    keep_alive_interval=30.0,           # WebSocket keepalive interval
    reconnect_attempts=5,               # Max reconnection attempts
    reconnect_delay=1.0,                # Initial reconnect delay
    max_queue_size=1000                 # Max subscription message queue
)
```

### Environment Variables

```bash
# Required
BIFROST_URL=ws://localhost:4000/graphql

# Optional
BIFROST_API_KEY=your_api_key
BIFROST_TIMEOUT=30
```

## API Reference

### BifrostClient Methods

#### `async query_tools(filters=None, limit=100) -> List[ToolMetadata]`
Query available tools from Bifrost.

**Parameters:**
- `filters` (dict, optional): Filter by category, tags, etc.
- `limit` (int): Maximum tools to return

**Returns:**
- `List[ToolMetadata]`: List of tool metadata

#### `async query_tool(name: str) -> Optional[ToolMetadata]`
Get metadata for specific tool.

**Parameters:**
- `name` (str): Tool name

**Returns:**
- `ToolMetadata` if found, `None` otherwise

#### `async route_request(prompt: str, context=None) -> RoutingDecision`
Get routing decision from Bifrost.

**Parameters:**
- `prompt` (str): User prompt
- `context` (dict, optional): Additional context

**Returns:**
- `RoutingDecision`: Selected tool, confidence, reasoning

#### `async execute_tool(name: str, input_data: dict) -> dict`
Execute tool via Bifrost.

**Parameters:**
- `name` (str): Tool name
- `input_data` (dict): Tool input parameters

**Returns:**
- `dict`: Execution result with `success`, `data`, `error`, `metadata`

#### `async semantic_search(query: str, limit=10, filters=None) -> List[SearchResult]`
Semantic search via Bifrost.

**Parameters:**
- `query` (str): Search query
- `limit` (int): Maximum results
- `filters` (dict, optional): Filter results

**Returns:**
- `List[SearchResult]`: Search results with scores

## Troubleshooting

### Client Not Connecting

```bash
# Check Bifrost is running
curl http://localhost:4000/health

# Check WebSocket endpoint
wscat -c ws://localhost:4000/graphql
```

### GraphQL Errors

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check GraphQL queries
logger.debug(f"Query: {query}")
logger.debug(f"Variables: {variables}")
```

### Subscription Issues

```python
# Check connection state
assert client.is_connected, "Client not connected"

# Check subscription count
print(f"Active subscriptions: {client.subscription_count}")

# Monitor connection state
client.state  # CONNECTED, DISCONNECTED, etc.
```

## Migration Guide

### Removing Local Business Logic

**Before:**
```python
# Local routing
from router import ArchRouter
router = ArchRouter()
result = await router.route(prompt)
```

**After:**
```python
# Bifrost routing
from bifrost_client import BifrostClient
client = BifrostClient()
result = await client.route_request(prompt)
```

### Updating Tests

**Before:**
```python
# Test local routing
def test_routing():
    router = ArchRouter()
    result = router.route("test")
    assert result.route == "entity_create"
```

**After:**
```python
# Test Bifrost delegation
async def test_routing(mock_bifrost):
    mock_bifrost.route_request.return_value = RoutingDecision(...)
    result = await app.post("/route", json={...})
    assert result.json()["route"] == "entity_create"
```

## Future Enhancements

- [ ] Batch queries/mutations
- [ ] Query result caching
- [ ] Automatic retry with exponential backoff
- [ ] Metrics and tracing integration
- [ ] Connection pooling for HTTP client
- [ ] GraphQL query validation
- [ ] Schema introspection
- [ ] Subscription reconnection improvements

## Related Documentation

- [GraphQLSubscriptionClient](./graphql_subscription_client.py) - Base WebSocket client
- [Bifrost Extensions SDK](./bifrost_extensions/README.md) - Bifrost SDK
- [SmartCP Architecture](./docs/ARCHITECTURE.md) - Overall architecture
