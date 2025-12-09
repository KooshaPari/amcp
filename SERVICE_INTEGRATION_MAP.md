# SmartCP Service Integration Map

**Date:** December 2, 2025
**Status:** ARCHITECTURAL REFERENCE
**Version:** 1.0.0

---

## System Overview

SmartCP is a multi-service architecture consisting of:
- **Python Services:** SmartCP API, Bifrost HTTP API, Router
- **Go Services:** Bifrost GraphQL Backend
- **Databases:** PostgreSQL, Neo4j, Redis
- **External Services:** OpenAI, Voyage AI, Supabase

---

## Service Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐          │
│  │   Browser   │  │     CLI      │  │  External Apps   │          │
│  │   (Swagger) │  │   (Typer)    │  │    (HTTP/REST)   │          │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘          │
│         │                │                    │                    │
│         └────────────────┴────────────────────┘                    │
│                          │                                         │
└──────────────────────────┼─────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       API GATEWAY LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │             SmartCP API (Python FastAPI)                  │    │
│  │                    Port: 8000                             │    │
│  │                                                           │    │
│  │  Endpoints:                                               │    │
│  │  - GET  /health          → Health check                  │    │
│  │  - GET  /api/v1/tools    → List MCP tools                │    │
│  │  - POST /api/v1/route    → Route query to model          │    │
│  │  - POST /api/v1/execute  → Execute tool                  │    │
│  │  - GET  /metrics         → Prometheus metrics            │    │
│  │  - GET  /docs            → Swagger UI                    │    │
│  └───────────────────┬───────────────────────────────────────┘    │
│                      │                                             │
│                      ├─────────────┬─────────────┐                │
│                      ↓             ↓             ↓                │
│         ┌────────────────┐ ┌───────────┐ ┌──────────────┐       │
│         │ BifrostClient  │ │   Auth    │ │   Router     │       │
│         │   (GraphQL)    │ │ Adapter   │ │  (Local)     │       │
│         └────────┬───────┘ └─────┬─────┘ └──────┬───────┘       │
│                  │                │               │               │
└──────────────────┼────────────────┼───────────────┼───────────────┘
                   │                │               │
                   ↓                ↓               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │       Bifrost HTTP API (Python FastAPI)                  │     │
│  │                 Port: 8001                                │     │
│  │                                                           │     │
│  │  Endpoints:                                               │     │
│  │  - POST /v1/route        → Model routing                 │     │
│  │  - POST /v1/route-tool   → Tool routing                  │     │
│  │  - POST /v1/classify     → Classification                │     │
│  │  - GET  /v1/usage        → Usage stats                   │     │
│  │  - GET  /health          → Health check                  │     │
│  └──────────────────────────┬───────────────────────────────┘     │
│                              │                                     │
│                              ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │     Bifrost GraphQL Backend (Go gqlgen)                  │     │
│  │                 Port: 8080                                │     │
│  │                                                           │     │
│  │  Endpoints:                                               │     │
│  │  - GET  /              → GraphQL Playground              │     │
│  │  - POST /query         → GraphQL queries/mutations       │     │
│  │  - WS   /query         → GraphQL subscriptions           │     │
│  │  - GET  /health        → Health check                    │     │
│  │  - GET  /metrics       → Prometheus metrics              │     │
│  │                                                           │     │
│  │  GraphQL Operations:                                      │     │
│  │  - query route(...)         → Route query                │     │
│  │  - query tools(...)         → List tools                 │     │
│  │  - query tool_by_id(...)    → Get tool                   │     │
│  │  - mutation execute_tool    → Execute tool               │     │
│  │  - subscription tool_events → Tool updates               │     │
│  └──────────────────┬───────────────────────────────────────┘     │
│                     │                                              │
│                     ↓                                              │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │              Router Module (Python)                      │     │
│  │            604 Python files, 200k+ LOC                   │     │
│  │                                                           │     │
│  │  Components:                                              │     │
│  │  - Unified Router        → 5 routing strategies          │     │
│  │  - Semantic Router       → ModernBERT embeddings         │     │
│  │  - Multi-hop Router      → Chained routing               │     │
│  │  - OpenRouter Client     → External model access         │     │
│  │  - Cost Optimizer        → Model cost analysis           │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   PostgreSQL    │  │      Redis      │  │      Neo4j      │   │
│  │   Port: 5432    │  │   Port: 6379    │  │  HTTP: 7474     │   │
│  │                 │  │                 │  │  Bolt: 7687     │   │
│  │  Tables:        │  │  Keys:          │  │  Graphs:        │   │
│  │  - tools        │  │  - route_cache  │  │  - relationships│   │
│  │  - routes_cache │  │  - tool_cache   │  │  - entities     │   │
│  │  - executions   │  │  - sessions     │  │  - workflows    │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │    OpenAI       │  │   Voyage AI     │  │    Supabase     │   │
│  │  (Embeddings)   │  │  (Embeddings)   │  │  (Persistence)  │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Service Details

### 1. SmartCP API (Python FastAPI)

**Purpose:** Main API gateway for external clients

**Technology Stack:**
- Python 3.10+
- FastAPI 0.121+
- Pydantic 2.0+
- Uvicorn (ASGI server)

**Port:** 8000

**Endpoints:**

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/health` | Health check | None |
| GET | `/api/v1/tools` | List MCP tools | API Key |
| POST | `/api/v1/route` | Route query to model | API Key |
| POST | `/api/v1/execute` | Execute tool | API Key |
| GET | `/metrics` | Prometheus metrics | None |
| GET | `/docs` | Swagger UI | None |

**Dependencies:**
- Bifrost GraphQL Backend (via GraphQL)
- PostgreSQL (direct)
- Redis (direct)
- Auth service (internal)

**Health Check:**
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

**Metrics:**
```bash
curl http://localhost:8000/metrics
# Prometheus format metrics
```

---

### 2. Bifrost HTTP API (Python FastAPI)

**Purpose:** HTTP wrapper for Bifrost SDK

**Technology Stack:**
- Python 3.10+
- FastAPI 0.121+
- Bifrost SDK (Python)

**Port:** 8001

**Endpoints:**

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/v1/route` | Model routing | API Key |
| POST | `/v1/route-tool` | Tool routing | API Key |
| POST | `/v1/classify` | Classification | API Key |
| GET | `/v1/usage` | Usage stats | API Key |
| GET | `/health` | Health check | None |

**Dependencies:**
- Bifrost GraphQL Backend (via SDK)
- Router module (internal)

**Health Check:**
```bash
curl http://localhost:8001/health
# Response: {"status": "ok"}
```

---

### 3. Bifrost GraphQL Backend (Go)

**Purpose:** Core routing and tool execution backend

**Technology Stack:**
- Go 1.21+
- gqlgen (GraphQL)
- PostgreSQL driver
- gRPC client

**Port:** 8080

**Endpoints:**

| Method | Path | Purpose | Protocol |
|--------|------|---------|----------|
| GET | `/` | GraphQL Playground | HTTP |
| POST | `/query` | GraphQL queries/mutations | GraphQL |
| WS | `/query` | GraphQL subscriptions | WebSocket |
| GET | `/health` | Health check | HTTP |
| GET | `/metrics` | Prometheus metrics | HTTP |

**GraphQL Schema:**

```graphql
type Query {
  # Routing
  route(input: RouteInput!): RouteResult!
  classify(query: String!): ClassificationResult!

  # Tools
  tools(category: String, limit: Int): [Tool!]!
  tool_by_id(id: ID!): Tool

  # Search
  semantic_search(query: String!, limit: Int): [SearchResult!]!

  # Usage
  usage_stats(startDate: String, endDate: String): UsageStats!

  # Health
  health: HealthStatus!
}

type Mutation {
  # Tool execution
  execute_tool(input: ExecuteToolInput!): ExecutionResult!

  # Tool registry
  register_tool(input: RegisterToolInput!): Tool!
  update_tool(id: ID!, input: UpdateToolInput!): Tool!
  delete_tool(id: ID!): Boolean!
}

type Subscription {
  # Real-time updates
  tool_events: ToolEvent!
  routing_events: RoutingEvent!
  execution_events: ExecutionEvent!
}
```

**Dependencies:**
- PostgreSQL (direct)
- Redis (for caching)
- MLX Service (via gRPC) - NOT IMPLEMENTED
- Router module (indirect via MLX)

**Health Check:**
```bash
curl http://localhost:8080/health
# Response: OK
```

**GraphQL Example:**
```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { health { status } }"
  }'
```

---

### 4. Router Module (Python)

**Purpose:** Model routing and tool selection logic

**Technology Stack:**
- Python 3.10+
- MLX (Apple Silicon optimization)
- Transformers (Hugging Face)
- ModernBERT embeddings

**Location:** `router/` directory (604 Python files)

**Components:**

| Component | Purpose | LOC |
|-----------|---------|-----|
| Unified Router | 5 routing strategies | 353 |
| Semantic Router | ModernBERT embeddings | 600+ |
| Multi-hop Router | Chained routing | 800+ |
| OpenRouter Client | External models | 500+ |
| Cost Optimizer | Model cost analysis | 200+ |

**Routing Strategies:**
1. **Model-based:** Choose model by capability
2. **Tool-based:** Choose tools by query
3. **Cost-optimized:** Minimize cost
4. **Latency-optimized:** Minimize latency
5. **Quality-optimized:** Maximize quality

**Dependencies:**
- OpenAI API (for embeddings)
- Voyage AI (for embeddings)
- Local MLX models

**Not Exposed:** Internal module, called by Bifrost backend

---

## Database Details

### PostgreSQL

**Purpose:** Primary data store for tools, routes, executions

**Port:** 5432

**Schema:**

```sql
-- Tools table
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100),
    capabilities JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Routes cache table
CREATE TABLE routes_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) NOT NULL UNIQUE,
    route VARCHAR(255) NOT NULL,
    tools JSONB DEFAULT '[]',
    confidence FLOAT,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Executions table
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id UUID REFERENCES tools(id),
    parameters JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    output TEXT,
    error TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes:**
- `idx_tools_category` on `tools(category)`
- `idx_tools_status` on `tools(status)`
- `idx_routes_cache_expires` on `routes_cache(expires_at)`
- `idx_executions_tool_id` on `executions(tool_id)`
- `idx_executions_status` on `executions(status)`

**Connections:**
- SmartCP API: Direct connection
- Bifrost Backend: Direct connection
- Connection pool: 25 max connections

**Health Check:**
```bash
docker-compose exec postgres pg_isready -U postgres
# Response: /var/run/postgresql:5432 - accepting connections
```

---

### Redis

**Purpose:** Caching layer for routing and tool queries

**Port:** 6379

**Key Patterns:**

| Pattern | Purpose | TTL |
|---------|---------|-----|
| `route:{hash}` | Route cache | 5 minutes |
| `tool:{id}` | Tool cache | 1 hour |
| `session:{id}` | Session data | 24 hours |
| `rate_limit:{key}` | Rate limiting | 1 minute |

**Eviction Policy:** `allkeys-lru` (Least Recently Used)

**Max Memory:** 256MB

**Connections:**
- SmartCP API: Direct connection
- Bifrost Backend: Direct connection

**Health Check:**
```bash
docker-compose exec redis redis-cli ping
# Response: PONG
```

---

### Neo4j

**Purpose:** Graph database for relationships and workflows

**Ports:**
- HTTP: 7474 (Browser)
- Bolt: 7687 (Protocol)

**Graph Model:**

```
(Tool)-[:REQUIRES]->(Tool)
(Tool)-[:PRODUCES]->(Entity)
(Entity)-[:RELATES_TO]->(Entity)
(Workflow)-[:CONTAINS]->(Tool)
```

**Connections:**
- SmartCP API: Bolt protocol
- Used for: Relationship queries, workflow tracking

**Health Check:**
```bash
curl -u neo4j:password http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"RETURN 1"}]}'
```

---

## Data Flow Diagrams

### Routing Flow

```
┌───────┐
│Client │
└───┬───┘
    │
    │ POST /api/v1/route { query: "..." }
    ↓
┌─────────────────┐
│  SmartCP API    │
│   (Port 8000)   │
└────────┬────────┘
         │
         │ GraphQL: query route(input: {...})
         ↓
┌─────────────────────┐
│ Bifrost Go Backend  │
│    (Port 8080)      │
│                     │
│ 1. Check cache      │────────→ Redis (route_cache)
│ 2. If miss, route   │
│ 3. Call router      │────────→ Router Module
│ 4. Store in cache   │────────→ Redis
│ 5. Store in DB      │────────→ PostgreSQL
│ 6. Return result    │
└────────┬────────────┘
         │
         │ RouteResult { route, tools, confidence }
         ↓
┌─────────────────┐
│  SmartCP API    │
└────────┬────────┘
         │
         │ JSON response
         ↓
┌───────┐
│Client │
└───────┘
```

### Tool Execution Flow

```
┌───────┐
│Client │
└───┬───┘
    │
    │ POST /api/v1/execute { tool_id, parameters }
    ↓
┌─────────────────┐
│  SmartCP API    │
└────────┬────────┘
         │
         │ GraphQL: mutation execute_tool(input: {...})
         ↓
┌─────────────────────┐
│ Bifrost Go Backend  │
│                     │
│ 1. Validate tool    │────────→ PostgreSQL (tools table)
│ 2. Execute tool     │────────→ Tool execution service
│ 3. Store execution  │────────→ PostgreSQL (executions table)
│ 4. Update graph     │────────→ Neo4j
│ 5. Return result    │
└────────┬────────────┘
         │
         │ ExecutionResult { id, status, output }
         ↓
┌─────────────────┐
│  SmartCP API    │
└────────┬────────┘
         │
         │ JSON response
         ↓
┌───────┐
│Client │
└───────┘
```

### Caching Strategy

```
┌─────────────────────┐
│   Incoming Request  │
└──────────┬──────────┘
           │
           ↓
      ┌────────┐
      │  Hash  │  (SHA256 of query + params)
      └────┬───┘
           │
           ↓
    ┌──────────────┐
    │ Redis Lookup │
    └──────┬───────┘
           │
     ┌─────┴─────┐
     ↓           ↓
  Cache Hit   Cache Miss
     │           │
     │           ↓
     │    ┌──────────────┐
     │    │ Compute Route│
     │    └──────┬───────┘
     │           │
     │           ↓
     │    ┌──────────────┐
     │    │  Store Redis │ (TTL: 5 min)
     │    └──────┬───────┘
     │           │
     │           ↓
     │    ┌──────────────┐
     │    │  Store PG    │ (Permanent)
     │    └──────┬───────┘
     │           │
     └───────────┘
           │
           ↓
    ┌──────────────┐
    │Return Result │
    └──────────────┘
```

---

## Network Configuration

### Port Mapping

| Service | Internal Port | External Port | Protocol | Purpose |
|---------|--------------|---------------|----------|---------|
| SmartCP API | 8000 | 8000 | HTTP | Main API |
| Bifrost HTTP API | 8001 | 8001 | HTTP | Bifrost HTTP wrapper |
| Bifrost Backend | 8080 | 8080 | HTTP/WS | GraphQL API |
| PostgreSQL | 5432 | 5432 | TCP | Database |
| Redis | 6379 | 6379 | TCP | Cache |
| Neo4j HTTP | 7474 | 7474 | HTTP | Browser UI |
| Neo4j Bolt | 7687 | 7687 | TCP | Bolt protocol |
| Prometheus | 9090 | 9090 | HTTP | Metrics scraping |

### DNS / Service Discovery

**Local Development:**
- Services accessible via `localhost:<port>`
- Docker network: `smartcp_network` (bridge)

**Docker Compose:**
- Services resolve by service name
- Example: `http://api:8000/health`

**Production:**
- Load balancer → SmartCP API
- Internal DNS → Backend services
- CDN → Static assets (if applicable)

---

## Security Architecture

### Authentication Flow

```
┌───────┐
│Client │
└───┬───┘
    │
    │ Request + Authorization: Bearer <token>
    ↓
┌─────────────────┐
│  API Gateway    │
│                 │
│ 1. Extract token│
│ 2. Validate JWT │
│ 3. Check API key│
│ 4. Check rate   │
│    limit        │
└────────┬────────┘
         │
         │ If valid, forward request
         │ If invalid, return 401
         ↓
┌─────────────────┐
│ Backend Service │
└─────────────────┘
```

### Security Headers

All services set these headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

### Rate Limiting

**Strategy:** Token bucket

**Limits:**
- Anonymous: 10 req/min
- Authenticated: 100 req/min
- Admin: 1000 req/min

**Implementation:**
- SmartCP API: middleware + Redis
- Bifrost Backend: middleware + Redis

---

## Monitoring Architecture

### Metrics Collection

```
┌─────────────────────────────────────────┐
│            Services                     │
│  (SmartCP API, Bifrost Backend, etc.)  │
│                                         │
│  Expose /metrics endpoint               │
└─────────────┬───────────────────────────┘
              │
              │ HTTP GET /metrics (pull)
              ↓
┌─────────────────────────────────────────┐
│          Prometheus Server              │
│         (Port 9090)                     │
│                                         │
│  - Scrape every 15 seconds              │
│  - Store time-series data               │
│  - Retention: 15 days                   │
└─────────────┬───────────────────────────┘
              │
              │ PromQL queries
              ↓
┌─────────────────────────────────────────┐
│            Grafana                      │
│         (Port 3000)                     │
│                                         │
│  Dashboards:                            │
│  - Service Overview                     │
│  - Performance Metrics                  │
│  - Error Tracking                       │
│  - Infrastructure                       │
└─────────────────────────────────────────┘
```

### Key Metrics

**SmartCP API:**
- `smartcp_requests_total{method, endpoint, status}`
- `smartcp_request_duration_seconds{method, endpoint}`
- `smartcp_active_requests`
- `smartcp_errors_total{endpoint, error_type}`

**Bifrost Backend:**
- `bifrost_routing_duration_seconds{strategy}`
- `bifrost_routing_cache_hits_total`
- `bifrost_tool_executions_total{tool, status}`
- `bifrost_graphql_requests_total{operation}`

**Infrastructure:**
- `postgres_connections_active`
- `redis_keys_total`
- `neo4j_queries_total`

---

## Disaster Recovery

### Backup Strategy

```
┌─────────────────┐
│   PostgreSQL    │
└────────┬────────┘
         │
         │ pg_dump (daily, automated)
         ↓
┌─────────────────┐
│  Backup Storage │
│   (S3/GCS)      │
│                 │
│  Retention:     │
│  - Daily: 7 days│
│  - Weekly: 4wks │
│  - Monthly: 1yr │
└─────────────────┘
```

### Failover Strategy

```
┌────────────────┐       ┌────────────────┐
│  Primary DB    │ ---→  │   Replica DB   │
│  (Read/Write)  │       │  (Read-only)   │
└────────┬───────┘       └────────┬───────┘
         │                        │
         │ If primary fails:      │
         │ 1. Detect failure      │
         │ 2. Promote replica     │
         │ 3. Update DNS          │
         │ 4. Resume operations   │
         │                        │
         └────────────────────────┘
              Failover time: < 5 minutes
```

---

## Conclusion

**Current Integration Status:**
- ✅ SmartCP API: Ready
- ✅ Bifrost HTTP API: Ready
- ✅ Router Module: Ready
- ❌ Bifrost Go Backend: NOT IMPLEMENTED
- ✅ Databases: Ready (schema needs migration)
- ✅ Docker Compose: Ready (needs validation)

**Critical Path:** Implement Bifrost Go Backend (See `GAPS_ANALYSIS.md` Gap 1)

**Timeline:** 2-3 weeks to full integration

---

**Last Updated:** December 2, 2025
**Status:** ARCHITECTURAL REFERENCE
**Version:** 1.0.0
