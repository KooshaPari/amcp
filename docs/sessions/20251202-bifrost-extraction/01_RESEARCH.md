# Research: SmartCP Business Logic Extraction

## Current SmartCP Architecture

### Line Count Analysis
```bash
Total SmartCP LOC: 13,498 lines

Top files by size:
- neo4j_storage_adapter.py: 790 lines (graph DB adapter)
- voyage_ai_integration.py: 761 lines (embeddings)
- graphql_subscription_client.py: 668 lines (GraphQL client)
- infra_common.py: 555 lines (infrastructure utilities)
- fastmcp_auth_enhancement.py: 473 lines (auth)
- fastmcp_auth_provider.py: 377 lines (auth provider)
- hierarchical_memory.py: 363 lines (memory system)
- main.py: 284 lines (FastAPI application)
```

### Business Logic Components

#### 1. Tool Routing (`router/arch_router.py`)
**Responsibility:** ML-based semantic routing using Arch Router 1.5B model
**Key Features:**
- MLX-optimized inference (<50ms on Apple Silicon)
- Semantic understanding of queries
- Result caching
- Preference learning

**Dependencies:**
- `mlx_lm` - MLX language models
- HuggingFace model: `katanemo/Arch-Router-1.5B`
- Custom caching layer

**Business Logic to Extract:**
```python
class ArchRouter:
    def route(query: str, routes: Dict) -> RoutingResult
    def load_model() -> None
    def _build_prompt(query: str, routes: Dict) -> str
    def _parse_response(response: str) -> RoutingResult
```

#### 2. Tool Registry (`router/tool_registry.py`)
**Responsibility:** Tool and route definition management
**Key Features:**
- Route registration
- Tool discovery
- Capability mapping
- CLI integration patterns

**Business Logic to Extract:**
```python
class ToolRegistry:
    def register_route(route_def: Dict) -> None
    def get_route(name: str) -> RouteDefinition
    def list_routes() -> List[str]
    def list_all_tools() -> List[str]
    def get_tools_for_route(route: str) -> List[str]
```

#### 3. Semantic Discovery (`hooks/semantic_discovery.py`)
**Responsibility:** Pre-discovery hook system for semantic tool matching
**Key Features:**
- Semantic similarity matching
- Tool capability analysis
- Context-aware recommendations

**Business Logic to Extract:**
```python
async def pre_discovery_hook(
    action: str,
    prompt: str,
    router: ArchRouter,
    registry: ToolRegistry,
    context: Optional[dict]
) -> DiscoveryResult
```

#### 4. Database Services (`services/`)
**Responsibility:** Multi-database access layer
**Databases:**
- PostgreSQL (relational + pgvector)
- Memgraph (graph DB)
- Qdrant (vector DB)
- Valkey (cache/queue)

**Business Logic to Extract:**
```python
class DatabaseService:
    async def connect() -> None
    async def disconnect() -> None
    async def health_check() -> Dict[str, bool]

class SearchService:
    async def semantic_search(embedding: List[float], limit: int) -> List[Dict]
    async def full_text_search(query: str, limit: int) -> List[Dict]
    async def hybrid_search(query_text: str, query_embedding: List[float], limit: int) -> List[Dict]
```

#### 5. ML/Embedding Services (`infrastructure/mlx_integration.py`)
**Responsibility:** MLX model management and embedding generation
**Key Features:**
- Model loading and caching
- Embedding generation
- Performance monitoring

**Business Logic to Extract:**
```python
class MLXModelManager:
    def load() -> None
    def get_stats() -> Dict[str, Any]

class EmbeddingManager:
    def generate_embedding(text: str) -> List[float]
```

### Current Data Flow

```
Client Request
    ↓
main.py (FastAPI)
    ↓
pre_discovery_hook()
    ↓
ArchRouter.route() ← MLX Model (local)
    ↓
ToolRegistry.get_route()
    ↓
SearchService.semantic_search() ← Database (local)
    ↓
Response
```

## Bifrost Backend Architecture

### Current Structure
- **Language:** Go
- **Core:** `/core/bifrost.go` (90KB, complex core logic)
- **Framework:** `/framework/` (config, storage, logging)
- **Providers:** `/core/providers/` (LLM provider integrations)
- **Schemas:** `/core/schemas/` (data models)
- **MCP:** `/core/mcp.go` (MCP integration)

### Router Core
Path: `/Users/kooshapari/temp-PRODVERCEL/485/API/smartcp/router/router_core/`

Key components:
- `unified/router.py` - Unified routing interface
- `unified/strategy.py` - Routing strategies
- `unified/provider_manager.py` - Provider management
- `infrastructure/nats_integration.py` - NATS messaging
- `monitoring/sentinel.py` - Monitoring

**Observation:** Router core is in Python (not Go). Need to verify Bifrost Go integration.

### GraphQL Support
**Current State:** No GraphQL schema found in Bifrost
**Required:** Need to add GraphQL layer to Bifrost

**Options:**
1. Add GraphQL Go library (e.g., gqlgen, graphql-go)
2. Create REST API and use GraphQL gateway
3. Use existing gRPC and add GraphQL gateway

**Recommended:** Use `gqlgen` for type-safe GraphQL in Go

## Integration Patterns

### SmartCP GraphQL Client
File: `graphql_subscription_client.py` (668 lines)

**Features:**
- WebSocket-based subscriptions
- Automatic reconnection
- Message queue with backpressure
- Type-safe handlers
- Supports graphql-ws protocol

**Key Classes:**
```python
class GraphQLSubscriptionClient:
    async def connect(url: str) -> None
    async def subscribe(query: str, variables: Dict, handler: Callable) -> str
    async def unsubscribe(subscription_id: str) -> None
    async def execute_query(query: str, variables: Dict) -> Dict
```

### Bifrost Client Pattern
File: `bifrost_client.py`

**Current Usage:**
```python
class BifrostClient:
    async def query(query: str, variables: Dict) -> Dict
    async def mutate(mutation: str, variables: Dict) -> Dict
    async def subscribe(subscription: str, variables: Dict, handler: Callable) -> str
```

## External Research

### GraphQL in Go
**Library:** `gqlgen` - https://gqlgen.com/
- Type-safe GraphQL server
- Schema-first approach
- Generated resolvers
- Subscriptions via WebSocket
- Widely used in production

**Alternative:** `graphql-go/graphql`
- More manual configuration
- Flexible but verbose
- Lower-level control

**Recommendation:** Use `gqlgen` for type safety and code generation

### MLX from Go
**Options:**
1. **Python microservice** (Recommended)
   - Keep MLX in Python
   - Expose via gRPC/REST
   - Go service calls Python for inference

2. **CGo binding** (Complex)
   - Bind to Python C API
   - High complexity
   - Maintenance burden

3. **ONNX Runtime** (Future consideration)
   - Export MLX model to ONNX
   - Use Go ONNX runtime
   - Better performance but conversion complexity

**Recommendation:** Python microservice for MLX inference

### Vector Search in Go
**Libraries:**
- `qdrant/go-client` - Official Qdrant client
- `pgvector/pgvector-go` - PostgreSQL pgvector
- Native Go vector operations

**Pattern:**
```go
import (
    "github.com/qdrant/go-client/qdrant"
)

func semanticSearch(embedding []float32, limit int) ([]Result, error) {
    client := qdrant.NewClient(url)
    results, err := client.Search(ctx, &qdrant.SearchPoints{
        CollectionName: "tools",
        Vector: embedding,
        Limit: limit,
    })
    return results, err
}
```

## Migration Strategy

### Phase 1: GraphQL Schema Design
1. Define schema for tool routing operations
2. Define schema for tool registry operations
3. Define schema for search operations
4. Define schema for execution operations

### Phase 2: Bifrost Service Implementation
1. Add gqlgen to Bifrost
2. Implement ToolRoutingService (Go)
3. Create Python microservice for MLX inference
4. Implement ToolRegistryService (Go)
5. Implement SemanticSearchService (Go)
6. Implement GraphQL resolvers

### Phase 3: SmartCP Refactoring
1. Update BifrostClient with new GraphQL operations
2. Replace ArchRouter calls with GraphQL queries
3. Replace direct DB access with GraphQL queries
4. Replace MLX calls with GraphQL queries
5. Remove unused dependencies

### Phase 4: Testing & Verification
1. Update integration tests
2. Verify LOC reduction
3. Performance benchmarking
4. End-to-end testing

## Precedents from Codebase

### Existing BifrostClient Usage
```python
# From router/arch_router.py
async def route_with_bifrost(query: str) -> RoutingResult:
    client = BifrostClient()
    result = await client.query("""
        query RouteQuery($query: String!) {
            route(query: $query) {
                route
                tools
                confidence
            }
        }
    """, {"query": query})
    return RoutingResult(**result["route"])
```

### Existing GraphQL Patterns
```python
# From graphql_subscription_client.py
async def subscribe_to_tool_updates():
    client = GraphQLSubscriptionClient()
    await client.connect("ws://bifrost:8080/graphql")

    subscription_id = await client.subscribe(
        query="""
            subscription ToolUpdates {
                toolRegistryUpdated {
                    tools {
                        name
                        capabilities
                    }
                }
            }
        """,
        handler=on_tool_update
    )
```

## Performance Considerations

### Current Performance
- **ArchRouter inference:** <50ms (MLX on Apple Silicon)
- **Database queries:** <100ms (local)
- **Embedding generation:** ~10ms per text

### Expected Performance with Bifrost
- **GraphQL round-trip:** ~5-10ms (localhost)
- **Service overhead:** ~5ms per service
- **Total latency:** ~20-30ms additional

**Mitigation Strategies:**
1. **Aggressive caching** - Cache routing decisions, embeddings
2. **Connection pooling** - Reuse GraphQL connections
3. **Batch operations** - Combine multiple queries
4. **Pre-warming** - Load models at startup
5. **Async execution** - Non-blocking operations

## References

### Documentation
- GraphQL spec: https://spec.graphql.org/
- gqlgen: https://gqlgen.com/
- MLX: https://github.com/ml-explore/mlx
- Qdrant Go client: https://github.com/qdrant/go-client

### Codebase Files
- `/Users/kooshapari/temp-PRODVERCEL/485/API/smartcp/main.py`
- `/Users/kooshapari/temp-PRODVERCEL/485/API/smartcp/router/arch_router.py`
- `/Users/kooshapari/temp-PRODVERCEL/485/API/smartcp/router/tool_registry.py`
- `/Users/kooshapari/temp-PRODVERCEL/485/API/smartcp/graphql_subscription_client.py`
- `/Users/kooshapari/temp-PRODVERCEL/485/API/bifrost/core/bifrost.go`
