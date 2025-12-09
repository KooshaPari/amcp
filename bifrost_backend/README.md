# Bifrost GraphQL Backend

Intelligent GraphQL routing layer for SmartCP - routes requests to appropriate MCP tools using semantic search and LLM-based analysis.

## Features

- **GraphQL API**: Query, mutation, and subscription support
- **Tool Registry**: Register and manage MCP tools
- **Intelligent Routing**: Route requests to appropriate tools with confidence scoring
- **Semantic Search**: Vector-based similarity search for tools
- **Tool Execution**: Execute tools with parameter validation
- **Real-time Events**: Subscribe to tool execution events via WebSocket

## Prerequisites

- Go 1.21 or higher
- PostgreSQL 14+ with pgvector extension
- (Optional) OpenAI API key for embeddings

## Quick Start

### 1. Setup Database

```sql
-- Create database
CREATE DATABASE bifrost;

-- Connect to database
\c bifrost

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tools table
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    input_schema JSONB NOT NULL,
    category TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    embedding vector(1536),  -- OpenAI embedding dimension
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Create indexes
CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_tags ON tools USING GIN(tags);
CREATE INDEX idx_tools_embedding ON tools USING ivfflat(embedding vector_cosine_ops);
CREATE INDEX idx_tools_created_at ON tools(created_at);
```

### 2. Set Environment Variables

```bash
# Required
export DATABASE_URL="postgres://user:password@localhost:5432/bifrost?sslmode=disable"

# Optional (for embeddings)
export EMBEDDING_ENDPOINT="https://api.openai.com/v1/embeddings"
export EMBEDDING_API_KEY="sk-..."

# Optional (for custom port)
export PORT="8080"
```

### 3. Generate GraphQL Code

```bash
# Install dependencies and generate code
./generate.sh

# Or manually:
go mod download
go run github.com/99designs/gqlgen generate
```

### 4. Build and Run

```bash
# Build binary
go build -o bifrost cmd/server/main.go

# Run binary
./bifrost

# Or run directly
go run cmd/server/main.go
```

Server starts on http://localhost:8080

## API Usage

### GraphQL Playground

Open http://localhost:8080 in your browser to access the GraphQL playground.

### Example Queries

**Register a Tool:**

```graphql
mutation {
  registerTool(input: {
    name: "create_entity"
    description: "Creates a new entity in the knowledge graph"
    inputSchema: "{\"type\":\"object\",\"properties\":{\"name\":{\"type\":\"string\"},\"type\":{\"type\":\"string\"}},\"required\":[\"name\"]}"
    category: "knowledge_graph"
    tags: ["entity", "create", "knowledge"]
  }) {
    id
    name
    description
    category
    tags
    createdAt
  }
}
```

**List Tools:**

```graphql
query {
  tools(category: "knowledge_graph", limit: 10) {
    id
    name
    description
    category
    tags
  }
}
```

**Route a Request:**

```graphql
query {
  route(request: "create a new entity named John") {
    toolId
    confidence
    reasoning
    tool {
      name
      description
    }
  }
}
```

**Semantic Search:**

```graphql
query {
  semanticSearch(query: "create entity", limit: 5, threshold: 0.7) {
    similarity
    ranking
    tool {
      name
      description
      category
    }
  }
}
```

**Execute a Tool:**

```graphql
mutation {
  executeTool(input: {
    toolId: "tool-uuid-here"
    parameters: "{\"name\":\"John\",\"type\":\"person\"}"
    context: "User requested entity creation"
  }) {
    success
    output
    error
    executionTime
  }
}
```

**Subscribe to Tool Events:**

```graphql
subscription {
  toolEvents {
    eventType
    timestamp
    tool {
      name
    }
    data
  }
}
```

### Health Check

```bash
curl http://localhost:8080/health
```

## Architecture

```
bifrost_backend/
├── cmd/
│   └── server/
│       └── main.go           # Application entry point
├── internal/
│   ├── db/
│   │   └── postgres.go       # Database layer
│   ├── graph/
│   │   ├── schema.graphqls   # GraphQL schema
│   │   ├── resolver.go       # Root resolver
│   │   └── generated.go      # Generated code (by gqlgen)
│   ├── models/
│   │   └── types.go          # Domain models
│   └── services/
│       ├── tool_registry.go  # Tool CRUD operations
│       ├── tool_routing.go   # Intelligent routing
│       ├── semantic_search.go # Vector search
│       └── execution.go      # Tool execution
├── go.mod                    # Go module
├── gqlgen.yml                # GraphQL codegen config
├── generate.sh               # Code generation script
└── README.md                 # This file
```

## Services

### Tool Registry
- Register new tools
- Update tool metadata
- Delete tools
- List/search tools by category and tags

### Tool Routing
- Analyze incoming requests
- Match to appropriate tools
- Score confidence for routing decisions
- Extract parameters from natural language

### Semantic Search
- Vector-based similarity search
- Embedding generation (optional)
- Fallback to keyword search
- Ranked results with similarity scores

### Execution Service
- Validate parameters against JSON schema
- Execute tools (mock or remote)
- Handle errors and timeouts
- Track execution metrics

## Development

### Run Tests

```bash
go test ./...
```

### Format Code

```bash
go fmt ./...
```

### Linting

```bash
go vet ./...
```

### Regenerate GraphQL Code

After modifying schema.graphqls:

```bash
go run github.com/99designs/gqlgen generate
```

## Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | - |
| `PORT` | No | Server port | 8080 |
| `EMBEDDING_ENDPOINT` | No | Embedding API endpoint | - |
| `EMBEDDING_API_KEY` | No | Embedding API key | - |

## Production Deployment

### Docker

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o bifrost cmd/server/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/bifrost .
EXPOSE 8080
CMD ["./bifrost"]
```

Build and run:

```bash
docker build -t bifrost .
docker run -p 8080:8080 \
  -e DATABASE_URL="postgres://..." \
  bifrost
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bifrost
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bifrost
  template:
    metadata:
      labels:
        app: bifrost
    spec:
      containers:
      - name: bifrost
        image: bifrost:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bifrost-secrets
              key: database-url
```

## Performance

- **Typical Response Time**: < 50ms for routing
- **Semantic Search**: < 100ms with embedding cache
- **Tool Execution**: Varies by tool
- **WebSocket Latency**: < 10ms

## Security

- Use environment variables for secrets
- Enable SSL/TLS in production
- Implement authentication middleware
- Rate limit GraphQL queries
- Validate all inputs
- Use prepared statements for SQL

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL

# Check pgvector extension
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### GraphQL Generation Errors

```bash
# Clean generated files
rm -rf internal/graph/generated.go internal/graph/model/

# Regenerate
go run github.com/99designs/gqlgen generate
```

### WebSocket Connection Issues

- Ensure no firewall blocking WebSocket connections
- Check Origin header in CORS settings
- Verify WebSocket upgrade headers

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests
4. Submit pull request

## License

MIT License - see LICENSE file for details
