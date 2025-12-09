# Specifications: Bifrost GraphQL API

## GraphQL Schema Design

### Complete Schema

```graphql
# ============================================================================
# Bifrost GraphQL Schema - Tool Routing & Discovery
# ============================================================================

# ----------------------------------------------------------------------------
# Scalar Types
# ----------------------------------------------------------------------------

scalar DateTime
scalar JSON
scalar Float32Array  # For embeddings

# ----------------------------------------------------------------------------
# Core Types
# ----------------------------------------------------------------------------

"""
Tool routing result with confidence scoring
"""
type RoutingResult {
  """Unique request ID for tracing"""
  id: ID!

  """Original query/prompt"""
  query: String!

  """Selected route name"""
  route: String!

  """List of tool identifiers for this route"""
  tools: [String!]!

  """CLI command to execute (if applicable)"""
  cliCommand: String

  """Active hooks for this route"""
  hooks: [String!]!

  """Confidence score (0.0-1.0)"""
  confidence: Float!

  """Whether result came from cache"""
  cached: Boolean!

  """Routing decision explanation"""
  reasoning: String

  """Processing time in milliseconds"""
  latencyMs: Int!

  """Timestamp of routing decision"""
  timestamp: DateTime!
}

"""
Tool definition with capabilities and metadata
"""
type Tool {
  """Unique tool identifier"""
  id: ID!

  """Tool name"""
  name: String!

  """Tool description"""
  description: String!

  """Tool category/domain"""
  category: String!

  """Tool capabilities (tags)"""
  capabilities: [String!]!

  """Tool metadata"""
  metadata: JSON!

  """Supported parameters"""
  parameters: [ToolParameter!]!

  """Usage examples"""
  examples: [ToolExample!]

  """Tool status"""
  status: ToolStatus!

  """Creation timestamp"""
  createdAt: DateTime!

  """Last update timestamp"""
  updatedAt: DateTime!
}

"""
Tool parameter definition
"""
type ToolParameter {
  """Parameter name"""
  name: String!

  """Parameter type"""
  type: String!

  """Parameter description"""
  description: String!

  """Whether parameter is required"""
  required: Boolean!

  """Default value (if any)"""
  defaultValue: JSON

  """Validation rules"""
  validation: JSON
}

"""
Tool usage example
"""
type ToolExample {
  """Example title"""
  title: String!

  """Example description"""
  description: String

  """Example input"""
  input: JSON!

  """Expected output"""
  output: JSON
}

"""
Tool status enumeration
"""
enum ToolStatus {
  ACTIVE
  DEPRECATED
  BETA
  DISABLED
}

"""
Route definition with associated tools
"""
type Route {
  """Unique route identifier"""
  id: ID!

  """Route name"""
  name: String!

  """Route description"""
  description: String!

  """Associated tools"""
  tools: [Tool!]!

  """Route patterns (for matching)"""
  patterns: [String!]!

  """Route priority (higher = more preferred)"""
  priority: Int!

  """Route status"""
  status: RouteStatus!

  """Creation timestamp"""
  createdAt: DateTime!

  """Last update timestamp"""
  updatedAt: DateTime!
}

"""
Route status enumeration
"""
enum RouteStatus {
  ACTIVE
  INACTIVE
  DEPRECATED
}

"""
Semantic search result
"""
type SearchResult {
  """Result ID"""
  id: ID!

  """Tool or route ID"""
  targetId: ID!

  """Result type (tool or route)"""
  targetType: SearchTargetType!

  """Result content"""
  content: String!

  """Similarity score (0.0-1.0)"""
  similarity: Float!

  """Result metadata"""
  metadata: JSON

  """Result timestamp"""
  timestamp: DateTime!
}

"""
Search target type
"""
enum SearchTargetType {
  TOOL
  ROUTE
  CAPABILITY
}

"""
Tool execution result
"""
type ExecutionResult {
  """Execution ID"""
  id: ID!

  """Tool ID"""
  toolId: ID!

  """Execution status"""
  status: ExecutionStatus!

  """Execution output"""
  output: JSON

  """Execution error (if any)"""
  error: String

  """Execution start time"""
  startedAt: DateTime!

  """Execution end time"""
  completedAt: DateTime

  """Execution duration in milliseconds"""
  durationMs: Int

  """Execution metadata"""
  metadata: JSON
}

"""
Execution status enumeration
"""
enum ExecutionStatus {
  PENDING
  RUNNING
  COMPLETED
  FAILED
  CANCELLED
}

"""
Model statistics
"""
type ModelStats {
  """Model name"""
  modelName: String!

  """Model status"""
  status: ModelStatus!

  """Total inference count"""
  totalInferences: Int!

  """Average inference time (ms)"""
  avgInferenceMs: Float!

  """Cache hit rate"""
  cacheHitRate: Float!

  """Last inference timestamp"""
  lastInference: DateTime

  """Model metadata"""
  metadata: JSON
}

"""
Model status enumeration
"""
enum ModelStatus {
  LOADED
  LOADING
  UNLOADED
  ERROR
}

"""
Health check status
"""
type HealthStatus {
  """Overall system health"""
  status: String!

  """Database health"""
  databases: DatabaseHealth!

  """Service health"""
  services: ServiceHealth!

  """Model health"""
  models: ModelHealth!

  """Last check timestamp"""
  timestamp: DateTime!
}

"""
Database health status
"""
type DatabaseHealth {
  """PostgreSQL status"""
  postgres: Boolean!

  """Memgraph status"""
  memgraph: Boolean!

  """Qdrant status"""
  qdrant: Boolean!

  """Valkey status"""
  valkey: Boolean!
}

"""
Service health status
"""
type ServiceHealth {
  """Routing service status"""
  routing: Boolean!

  """Registry service status"""
  registry: Boolean!

  """Search service status"""
  search: Boolean!

  """Execution service status"""
  execution: Boolean!

  """MLX service status"""
  mlx: Boolean!
}

"""
Model health status
"""
type ModelHealth {
  """Arch Router 1.5B status"""
  archRouter: Boolean!

  """Embedding model status"""
  embedding: Boolean!
}

# ----------------------------------------------------------------------------
# Input Types
# ----------------------------------------------------------------------------

"""
Routing request input
"""
input RoutingInput {
  """Query or prompt to route"""
  query: String!

  """Optional context"""
  context: JSON

  """Whether to use cache"""
  useCache: Boolean = true

  """Maximum number of routes to return"""
  maxRoutes: Int = 1
}

"""
Search input
"""
input SearchInput {
  """Search query"""
  query: String!

  """Search target types"""
  targetTypes: [SearchTargetType!]

  """Maximum results"""
  limit: Int = 10

  """Minimum similarity threshold"""
  threshold: Float = 0.7

  """Search filters"""
  filters: JSON
}

"""
Tool execution input
"""
input ExecutionInput {
  """Tool ID to execute"""
  toolId: ID!

  """Execution parameters"""
  parameters: JSON!

  """Execution options"""
  options: JSON
}

"""
Tool registration input
"""
input ToolInput {
  """Tool name"""
  name: String!

  """Tool description"""
  description: String!

  """Tool category"""
  category: String!

  """Tool capabilities"""
  capabilities: [String!]!

  """Tool metadata"""
  metadata: JSON

  """Tool parameters"""
  parameters: [ToolParameterInput!]!

  """Tool examples"""
  examples: [ToolExampleInput!]

  """Tool status"""
  status: ToolStatus = ACTIVE
}

"""
Tool parameter input
"""
input ToolParameterInput {
  """Parameter name"""
  name: String!

  """Parameter type"""
  type: String!

  """Parameter description"""
  description: String!

  """Whether parameter is required"""
  required: Boolean!

  """Default value"""
  defaultValue: JSON

  """Validation rules"""
  validation: JSON
}

"""
Tool example input
"""
input ToolExampleInput {
  """Example title"""
  title: String!

  """Example description"""
  description: String

  """Example input"""
  input: JSON!

  """Expected output"""
  output: JSON
}

"""
Route registration input
"""
input RouteInput {
  """Route name"""
  name: String!

  """Route description"""
  description: String!

  """Associated tool IDs"""
  toolIds: [ID!]!

  """Route patterns"""
  patterns: [String!]!

  """Route priority"""
  priority: Int = 0

  """Route status"""
  status: RouteStatus = ACTIVE
}

# ----------------------------------------------------------------------------
# Queries
# ----------------------------------------------------------------------------

type Query {
  """
  Route a query to appropriate tools
  """
  route(input: RoutingInput!): RoutingResult!

  """
  Get all available routes
  """
  routes(
    """Filter by status"""
    status: RouteStatus

    """Pagination limit"""
    limit: Int = 100

    """Pagination offset"""
    offset: Int = 0
  ): [Route!]!

  """
  Get route by ID or name
  """
  route_by_id(
    """Route ID"""
    id: ID

    """Route name"""
    name: String
  ): Route

  """
  Get all available tools
  """
  tools(
    """Filter by category"""
    category: String

    """Filter by status"""
    status: ToolStatus

    """Pagination limit"""
    limit: Int = 100

    """Pagination offset"""
    offset: Int = 0
  ): [Tool!]!

  """
  Get tool by ID or name
  """
  tool_by_id(
    """Tool ID"""
    id: ID

    """Tool name"""
    name: String
  ): Tool

  """
  Semantic search for tools/routes
  """
  semantic_search(input: SearchInput!): [SearchResult!]!

  """
  Full-text search for tools/routes
  """
  fulltext_search(
    """Search query"""
    query: String!

    """Maximum results"""
    limit: Int = 10
  ): [SearchResult!]!

  """
  Hybrid search (semantic + fulltext)
  """
  hybrid_search(input: SearchInput!): [SearchResult!]!

  """
  Get execution result
  """
  execution(id: ID!): ExecutionResult

  """
  Get model statistics
  """
  model_stats(
    """Model name"""
    modelName: String
  ): [ModelStats!]!

  """
  Health check
  """
  health: HealthStatus!
}

# ----------------------------------------------------------------------------
# Mutations
# ----------------------------------------------------------------------------

type Mutation {
  """
  Register a new tool
  """
  register_tool(input: ToolInput!): Tool!

  """
  Update an existing tool
  """
  update_tool(
    """Tool ID"""
    id: ID!

    """Updated tool data"""
    input: ToolInput!
  ): Tool!

  """
  Delete a tool
  """
  delete_tool(id: ID!): Boolean!

  """
  Register a new route
  """
  register_route(input: RouteInput!): Route!

  """
  Update an existing route
  """
  update_route(
    """Route ID"""
    id: ID!

    """Updated route data"""
    input: RouteInput!
  ): Route!

  """
  Delete a route
  """
  delete_route(id: ID!): Boolean!

  """
  Execute a tool
  """
  execute_tool(input: ExecutionInput!): ExecutionResult!

  """
  Cancel a running execution
  """
  cancel_execution(id: ID!): Boolean!

  """
  Clear routing cache
  """
  clear_cache: Boolean!

  """
  Reload ML models
  """
  reload_models: Boolean!
}

# ----------------------------------------------------------------------------
# Subscriptions
# ----------------------------------------------------------------------------

type Subscription {
  """
  Subscribe to tool registry updates
  """
  tool_registry_updated: Tool!

  """
  Subscribe to route registry updates
  """
  route_registry_updated: Route!

  """
  Subscribe to execution updates
  """
  execution_updated(
    """Execution ID to track"""
    id: ID!
  ): ExecutionResult!

  """
  Subscribe to model status updates
  """
  model_status_updated: ModelStats!
}
```

## API Contracts

### Query: `route`
**Purpose:** Route a query to appropriate tools using ML-based routing

**Input:**
```graphql
{
  query: String!
  context: JSON
  useCache: Boolean
  maxRoutes: Int
}
```

**Output:**
```graphql
{
  id: ID!
  query: String!
  route: String!
  tools: [String!]!
  cliCommand: String
  hooks: [String!]!
  confidence: Float!
  cached: Boolean!
  reasoning: String
  latencyMs: Int!
  timestamp: DateTime!
}
```

**Example:**
```graphql
query RouteQuery {
  route(input: {
    query: "List all files in the current directory"
    useCache: true
  }) {
    route
    tools
    confidence
    reasoning
  }
}
```

**Response:**
```json
{
  "data": {
    "route": {
      "route": "filesystem",
      "tools": ["ls", "find", "tree"],
      "confidence": 0.95,
      "reasoning": "Query explicitly mentions listing files, filesystem route is best match"
    }
  }
}
```

### Query: `semantic_search`
**Purpose:** Search for tools/routes using semantic similarity

**Input:**
```graphql
{
  query: String!
  targetTypes: [SearchTargetType!]
  limit: Int
  threshold: Float
  filters: JSON
}
```

**Output:**
```graphql
[{
  id: ID!
  targetId: ID!
  targetType: SearchTargetType!
  content: String!
  similarity: Float!
  metadata: JSON
  timestamp: DateTime!
}]
```

**Example:**
```graphql
query SemanticSearch {
  semantic_search(input: {
    query: "read file contents"
    targetTypes: [TOOL]
    limit: 5
    threshold: 0.8
  }) {
    targetId
    content
    similarity
  }
}
```

### Mutation: `execute_tool`
**Purpose:** Execute a tool with parameters

**Input:**
```graphql
{
  toolId: ID!
  parameters: JSON!
  options: JSON
}
```

**Output:**
```graphql
{
  id: ID!
  toolId: ID!
  status: ExecutionStatus!
  output: JSON
  error: String
  startedAt: DateTime!
  completedAt: DateTime
  durationMs: Int
  metadata: JSON
}
```

**Example:**
```graphql
mutation ExecuteTool {
  execute_tool(input: {
    toolId: "ls"
    parameters: {
      path: "/home/user"
      flags: ["-la"]
    }
  }) {
    id
    status
    output
    durationMs
  }
}
```

### Subscription: `tool_registry_updated`
**Purpose:** Real-time updates when tools are registered/updated/deleted

**Output:**
```graphql
{
  id: ID!
  name: String!
  description: String!
  category: String!
  capabilities: [String!]!
  status: ToolStatus!
  updatedAt: DateTime!
}
```

**Example:**
```graphql
subscription ToolUpdates {
  tool_registry_updated {
    id
    name
    capabilities
    status
  }
}
```

## Acceptance Criteria

### Functional Requirements

1. **Routing Operations**
   - [ ] `route` query returns routing decisions with >95% accuracy
   - [ ] Routing uses ML model (Arch Router 1.5B)
   - [ ] Caching works correctly (cache hits <5ms)
   - [ ] Confidence scores accurate (0.0-1.0 range)

2. **Tool Registry Operations**
   - [ ] `tools` query returns all active tools
   - [ ] `tool_by_id` query returns specific tool
   - [ ] `register_tool` mutation creates new tool
   - [ ] `update_tool` mutation updates existing tool
   - [ ] `delete_tool` mutation removes tool

3. **Route Registry Operations**
   - [ ] `routes` query returns all active routes
   - [ ] `route_by_id` query returns specific route
   - [ ] `register_route` mutation creates new route
   - [ ] `update_route` mutation updates existing route
   - [ ] `delete_route` mutation removes route

4. **Search Operations**
   - [ ] `semantic_search` returns relevant results
   - [ ] `fulltext_search` supports PostgreSQL FTS
   - [ ] `hybrid_search` combines both methods
   - [ ] Search respects similarity threshold
   - [ ] Results sorted by relevance

5. **Execution Operations**
   - [ ] `execute_tool` runs tools asynchronously
   - [ ] `execution` query returns status/results
   - [ ] `cancel_execution` stops running executions
   - [ ] Execution errors handled gracefully

6. **Subscriptions**
   - [ ] `tool_registry_updated` fires on registry changes
   - [ ] `route_registry_updated` fires on route changes
   - [ ] `execution_updated` tracks execution progress
   - [ ] Subscriptions support reconnection

7. **Health & Monitoring**
   - [ ] `health` query checks all services
   - [ ] `model_stats` returns ML model metrics
   - [ ] Health checks include database status
   - [ ] Model statistics updated in real-time

### Non-Functional Requirements

1. **Performance**
   - [ ] Routing queries complete in <50ms
   - [ ] Search queries complete in <100ms
   - [ ] GraphQL overhead <10ms
   - [ ] Subscriptions support 1000+ concurrent connections

2. **Reliability**
   - [ ] 99.9% uptime for routing service
   - [ ] Automatic reconnection on failures
   - [ ] Graceful degradation when ML unavailable
   - [ ] Circuit breaker for failing services

3. **Security**
   - [ ] Authentication required for mutations
   - [ ] Rate limiting on queries (100/min per user)
   - [ ] Input validation on all fields
   - [ ] SQL injection prevention

4. **Observability**
   - [ ] All operations logged
   - [ ] Distributed tracing support
   - [ ] Metrics exported (Prometheus format)
   - [ ] Error tracking integrated

## ARUs (Assumptions, Risks, Uncertainties)

### Assumptions
- GraphQL schema is sufficient for all SmartCP operations
- ML inference latency acceptable via network call
- Bifrost can support GraphQL subscriptions
- Database schemas support required queries

### Risks
- **Network latency** - MITIGATION: Aggressive caching, batch operations
- **ML model loading time** - MITIGATION: Pre-warm at startup, keep loaded
- **Subscription scalability** - MITIGATION: Use NATS for pub/sub, limit connections
- **Schema evolution** - MITIGATION: Versioned schema, deprecation warnings

### Uncertainties
- Optimal cache TTL for routing decisions
- Best embedding model for semantic search
- Subscription message format details
- Error handling conventions
