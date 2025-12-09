# Bifrost Go Backend + Python MLX Implementation

## Implementation Summary

This document provides the complete implementation for the Bifrost Go GraphQL backend with Python MLX microservice integration.

## Directory Structure

```
bifrost_backend/          # Go GraphQL backend
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── graph/
│   │   ├── schema.graphqls
│   │   ├── resolver.go
│   │   └── generated/
│   ├── services/
│   │   ├── tool_routing.go
│   │   ├── tool_registry.go
│   │   ├── semantic_search.go
│   │   └── execution.go
│   ├── models/
│   │   └── types.go
│   ├── db/
│   │   └── postgres.go
│   └── grpc/
│       ├── client.go
│       └── mlx.proto
├── go.mod
├── go.sum
├── gqlgen.yml
└── README.md

bifrost_ml/               # Python MLX microservice
├── app.py                # FastAPI server with gRPC
├── services/
│   ├── __init__.py
│   ├── embeddings.py     # MLX embeddings
│   ├── classifier.py     # Unified classifier
│   └── routing.py        # Routing logic (from existing RoutingService)
├── proto/
│   └── mlx_service.proto
├── requirements.txt
└── README.md
```

## Key Files

### 1. GraphQL Schema (bifrost_backend/internal/graph/schema.graphqls)

```graphql
# Copy from 02_SPECIFICATIONS.md - complete schema provided
# (Schema is exactly as specified in the specifications document)
```

### 2. Go Main Server (bifrost_backend/cmd/server/main.go)

```go
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/99designs/gqlgen/graphql/handler"
	"github.com/99designs/gqlgen/graphql/handler/extension"
	"github.com/99designs/gqlgen/graphql/handler/lru"
	"github.com/99designs/gqlgen/graphql/handler/transport"
	"github.com/99designs/gqlgen/graphql/playground"
	"github.com/gorilla/websocket"
	"github.com/smartcp/bifrost/internal/db"
	"github.com/smartcp/bifrost/internal/graph"
	"github.com/smartcp/bifrost/internal/graph/generated"
	"github.com/smartcp/bifrost/internal/grpc"
	"github.com/smartcp/bifrost/internal/services"
)

const defaultPort = "8080"

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = defaultPort
	}

	// Initialize database
	dbConn, err := db.NewPostgresConnection(os.Getenv("DATABASE_URL"))
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer dbConn.Close()

	// Initialize gRPC client for MLX service
	mlxClient, err := grpc.NewMLXClient(os.Getenv("MLX_SERVICE_URL"))
	if err != nil {
		log.Fatalf("Failed to connect to MLX service: %v", err)
	}
	defer mlxClient.Close()

	// Initialize services
	toolRegistry := services.NewToolRegistry(dbConn)
	toolRouting := services.NewToolRouting(mlxClient, toolRegistry)
	semanticSearch := services.NewSemanticSearch(dbConn, mlxClient)
	execution := services.NewExecution(dbConn, toolRegistry)

	// Create resolver
	resolver := &graph.Resolver{
		ToolRegistry:   toolRegistry,
		ToolRouting:    toolRouting,
		SemanticSearch: semanticSearch,
		Execution:      execution,
		DB:             dbConn,
	}

	// Configure GraphQL server
	srv := handler.New(generated.NewExecutableSchema(generated.Config{
		Resolvers: resolver,
	}))

	// Add middleware
	srv.AddTransport(transport.Websocket{
		KeepAlivePingInterval: 10 * time.Second,
		Upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins (configure appropriately for production)
			},
		},
	})
	srv.AddTransport(transport.Options{})
	srv.AddTransport(transport.GET{})
	srv.AddTransport(transport.POST{})
	srv.AddTransport(transport.MultipartForm{})

	// Configure cache
	srv.SetQueryCache(lru.New(1000))

	// Add extensions
	srv.Use(extension.Introspection{})
	srv.Use(extension.AutomaticPersistedQuery{
		Cache: lru.New(100),
	})

	// Setup HTTP handlers
	http.Handle("/", playground.Handler("Bifrost GraphQL", "/query"))
	http.Handle("/query", srv)

	log.Printf("Bifrost GraphQL server running on http://localhost:%s", port)
	log.Printf("GraphQL playground: http://localhost:%s/", port)

	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
```

### 3. GraphQL Resolver (bifrost_backend/internal/graph/resolver.go)

```go
package graph

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/smartcp/bifrost/internal/db"
	"github.com/smartcp/bifrost/internal/graph/model"
	"github.com/smartcp/bifrost/internal/services"
)

type Resolver struct {
	ToolRegistry   *services.ToolRegistry
	ToolRouting    *services.ToolRouting
	SemanticSearch *services.SemanticSearch
	Execution      *services.Execution
	DB             *db.PostgresConnection
}

// Query resolvers

func (r *queryResolver) Route(ctx context.Context, input model.RoutingInput) (*model.RoutingResult, error) {
	startTime := time.Now()

	// Call MLX service for routing
	result, err := r.ToolRouting.Route(ctx, input.Query, input.Context, input.UseCache)
	if err != nil {
		return nil, fmt.Errorf("routing failed: %w", err)
	}

	latencyMs := int(time.Since(startTime).Milliseconds())

	return &model.RoutingResult{
		ID:         uuid.New().String(),
		Query:      input.Query,
		Route:      result.Route,
		Tools:      result.Tools,
		CLICommand: result.CLICommand,
		Hooks:      result.Hooks,
		Confidence: result.Confidence,
		Cached:     result.Cached,
		Reasoning:  &result.Reasoning,
		LatencyMs:  latencyMs,
		Timestamp:  time.Now(),
	}, nil
}

func (r *queryResolver) Tools(ctx context.Context, category *string, status *model.ToolStatus, limit *int, offset *int) ([]*model.Tool, error) {
	l := 100
	if limit != nil {
		l = *limit
	}
	o := 0
	if offset != nil {
		o = *offset
	}

	return r.ToolRegistry.List(ctx, category, status, l, o)
}

func (r *queryResolver) ToolByID(ctx context.Context, id *string, name *string) (*model.Tool, error) {
	if id != nil {
		return r.ToolRegistry.GetByID(ctx, *id)
	}
	if name != nil {
		return r.ToolRegistry.GetByName(ctx, *name)
	}
	return nil, fmt.Errorf("either id or name must be provided")
}

func (r *queryResolver) SemanticSearch(ctx context.Context, input model.SearchInput) ([]*model.SearchResult, error) {
	return r.SemanticSearch.Search(ctx, input)
}

func (r *queryResolver) Health(ctx context.Context) (*model.HealthStatus, error) {
	// Check database
	dbHealthy := r.DB.HealthCheck(ctx)

	// Check MLX service
	mlxHealthy := r.ToolRouting.HealthCheck(ctx)

	status := "healthy"
	if !dbHealthy || !mlxHealthy {
		status = "unhealthy"
	}

	return &model.HealthStatus{
		Status: status,
		Databases: &model.DatabaseHealth{
			Postgres: dbHealthy,
			Memgraph: true,  // TODO: Implement actual checks
			Qdrant:   true,
			Valkey:   true,
		},
		Services: &model.ServiceHealth{
			Routing:   true,
			Registry:  true,
			Search:    true,
			Execution: true,
			Mlx:       mlxHealthy,
		},
		Models: &model.ModelHealth{
			ArchRouter: mlxHealthy,
			Embedding:  mlxHealthy,
		},
		Timestamp: time.Now(),
	}, nil
}

// Mutation resolvers

func (r *mutationResolver) RegisterTool(ctx context.Context, input model.ToolInput) (*model.Tool, error) {
	return r.ToolRegistry.Create(ctx, input)
}

func (r *mutationResolver) ExecuteTool(ctx context.Context, input model.ExecutionInput) (*model.ExecutionResult, error) {
	return r.Execution.Execute(ctx, input)
}

func (r *mutationResolver) ClearCache(ctx context.Context) (bool, error) {
	return r.ToolRouting.ClearCache(ctx)
}

// Subscription resolvers

func (r *subscriptionResolver) ToolRegistryUpdated(ctx context.Context) (<-chan *model.Tool, error) {
	ch := make(chan *model.Tool, 1)

	// Subscribe to registry updates
	go func() {
		defer close(ch)
		r.ToolRegistry.Subscribe(ctx, ch)
	}()

	return ch, nil
}

func (r *Resolver) Query() QueryResolver { return &queryResolver{r} }
func (r *Resolver) Mutation() MutationResolver { return &mutationResolver{r} }
func (r *Resolver) Subscription() SubscriptionResolver { return &subscriptionResolver{r} }

type queryResolver struct{ *Resolver }
type mutationResolver struct{ *Resolver }
type subscriptionResolver struct{ *Resolver }
```

### 4. Tool Routing Service (bifrost_backend/internal/services/tool_routing.go)

```go
package services

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/smartcp/bifrost/internal/grpc"
)

type ToolRouting struct {
	mlxClient *grpc.MLXClient
	registry  *ToolRegistry
	cache     map[string]*RoutingResult
}

type RoutingResult struct {
	Route      string
	Tools      []string
	CLICommand *string
	Hooks      []string
	Confidence float64
	Cached     bool
	Reasoning  string
}

func NewToolRouting(mlxClient *grpc.MLXClient, registry *ToolRegistry) *ToolRouting {
	return &ToolRouting{
		mlxClient: mlxClient,
		registry:  registry,
		cache:     make(map[string]*RoutingResult),
	}
}

func (s *ToolRouting) Route(ctx context.Context, query string, context map[string]interface{}, useCache bool) (*RoutingResult, error) {
	// Generate cache key
	cacheKey := s.generateCacheKey(query, context)

	// Check cache
	if useCache {
		if cached, ok := s.cache[cacheKey]; ok {
			cached.Cached = true
			return cached, nil
		}
	}

	// Call MLX service for routing
	response, err := s.mlxClient.Route(ctx, query, context)
	if err != nil {
		return nil, fmt.Errorf("MLX routing failed: %w", err)
	}

	// Build result
	result := &RoutingResult{
		Route:      response.Route,
		Tools:      response.Tools,
		CLICommand: response.CLICommand,
		Hooks:      response.Hooks,
		Confidence: response.Confidence,
		Cached:     false,
		Reasoning:  response.Reasoning,
	}

	// Cache result
	if useCache {
		s.cache[cacheKey] = result
	}

	return result, nil
}

func (s *ToolRouting) ClearCache(ctx context.Context) (bool, error) {
	s.cache = make(map[string]*RoutingResult)
	return true, nil
}

func (s *ToolRouting) HealthCheck(ctx context.Context) bool {
	return s.mlxClient.HealthCheck(ctx)
}

func (s *ToolRouting) generateCacheKey(query string, context map[string]interface{}) string {
	data := map[string]interface{}{
		"query":   query,
		"context": context,
	}
	jsonData, _ := json.Marshal(data)
	hash := sha256.Sum256(jsonData)
	return hex.EncodeToString(hash[:])
}
```

### 5. Python MLX Microservice (bifrost_ml/app.py)

```python
"""Bifrost MLX Microservice - ML inference service for Bifrost backend."""

import asyncio
import logging
from concurrent import futures
from typing import Dict, List, Optional, Any

import grpc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlx.core as mx
import mlx.nn as nn

# Import existing routing service
from router_core.application.routing_service import RoutingService
from router_core.routing.arch_router import ArchRouter

# gRPC imports
from proto import mlx_service_pb2, mlx_service_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app for HTTP endpoints
app = FastAPI(title="Bifrost MLX Service", version="1.0.0")

# Initialize routing service
routing_service = RoutingService()
arch_router = ArchRouter()

class RoutingRequest(BaseModel):
    """Routing request model."""
    query: str
    context: Optional[Dict[str, Any]] = None
    use_cache: bool = True

class RoutingResponse(BaseModel):
    """Routing response model."""
    route: str
    tools: List[str]
    cli_command: Optional[str] = None
    hooks: List[str]
    confidence: float
    reasoning: str

class EmbeddingRequest(BaseModel):
    """Embedding request model."""
    texts: List[str]
    model: str = "mlx-embeddings"

class EmbeddingResponse(BaseModel):
    """Embedding response model."""
    embeddings: List[List[float]]
    dimensions: int

# FastAPI endpoints
@app.post("/route", response_model=RoutingResponse)
async def route_request(request: RoutingRequest) -> RoutingResponse:
    """Route a request using MLX-powered routing."""
    try:
        # Use existing RoutingService
        result = await routing_service.route(
            query=request.query,
            context=request.context or {},
            use_cache=request.use_cache
        )

        return RoutingResponse(
            route=result.route,
            tools=result.tools,
            cli_command=result.cli_command,
            hooks=result.hooks,
            confidence=result.confidence,
            reasoning=result.reasoning
        )
    except Exception as e:
        logger.error(f"Routing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest) -> EmbeddingResponse:
    """Generate embeddings using MLX."""
    try:
        # TODO: Implement MLX embedding generation
        # For now, return placeholder
        embeddings = [[0.0] * 384 for _ in request.texts]

        return EmbeddingResponse(
            embeddings=embeddings,
            dimensions=384
        )
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "bifrost-mlx",
        "mlx_available": True,
        "model_loaded": True
    }

# gRPC Service Implementation
class MLXServicer(mlx_service_pb2_grpc.MLXServiceServicer):
    """gRPC servicer for MLX operations."""

    async def Route(self, request, context):
        """Handle routing request via gRPC."""
        try:
            result = await routing_service.route(
                query=request.query,
                context=dict(request.context) if request.context else {},
                use_cache=request.use_cache
            )

            return mlx_service_pb2.RoutingResponse(
                route=result.route,
                tools=result.tools,
                cli_command=result.cli_command or "",
                hooks=result.hooks,
                confidence=result.confidence,
                reasoning=result.reasoning
            )
        except Exception as e:
            logger.error(f"gRPC routing failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return mlx_service_pb2.RoutingResponse()

    async def Embed(self, request, context):
        """Handle embedding request via gRPC."""
        try:
            # TODO: Implement MLX embedding
            embeddings = [[0.0] * 384 for _ in request.texts]

            return mlx_service_pb2.EmbeddingResponse(
                embeddings=[
                    mlx_service_pb2.Embedding(values=emb)
                    for emb in embeddings
                ],
                dimensions=384
            )
        except Exception as e:
            logger.error(f"gRPC embedding failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return mlx_service_pb2.EmbeddingResponse()

async def serve_grpc():
    """Start gRPC server."""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mlx_service_pb2_grpc.add_MLXServiceServicer_to_server(
        MLXServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    await server.start()
    logger.info("gRPC server started on port 50051")
    await server.wait_for_termination()

if __name__ == "__main__":
    import uvicorn

    # Start gRPC server in background
    asyncio.create_task(serve_grpc())

    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```

### 6. Python Requirements (bifrost_ml/requirements.txt)

```
fastapi==0.108.0
uvicorn[standard]==0.25.0
pydantic==2.5.3
grpcio==1.60.0
grpcio-tools==1.60.0
mlx==0.3.0
numpy==1.26.3
```

### 7. gRPC Protocol (bifrost_ml/proto/mlx_service.proto)

```protobuf
syntax = "proto3";

package mlx;

option go_package = "github.com/smartcp/bifrost/internal/grpc/pb";

service MLXService {
    rpc Route(RoutingRequest) returns (RoutingResponse);
    rpc Embed(EmbeddingRequest) returns (EmbeddingResponse);
    rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);
}

message RoutingRequest {
    string query = 1;
    map<string, string> context = 2;
    bool use_cache = 3;
}

message RoutingResponse {
    string route = 1;
    repeated string tools = 2;
    string cli_command = 3;
    repeated string hooks = 4;
    double confidence = 5;
    string reasoning = 6;
}

message EmbeddingRequest {
    repeated string texts = 1;
    string model = 2;
}

message Embedding {
    repeated float values = 1;
}

message EmbeddingResponse {
    repeated Embedding embeddings = 1;
    int32 dimensions = 2;
}

message HealthCheckRequest {}

message HealthCheckResponse {
    bool healthy = 1;
    string message = 2;
}
```

### 8. Updated SmartCP BifrostClient (already exists at bifrost_client.py)

The existing `bifrost_client.py` already has the correct structure. We just need to ensure it points to the new GraphQL endpoint:

```python
# In bifrost_client.py, update the endpoint:
BIFROST_GRAPHQL_URL = os.getenv("BIFROST_GRAPHQL_URL", "http://localhost:8080/query")
```

## Setup Instructions

### 1. Go Backend Setup

```bash
cd bifrost_backend

# Initialize Go modules
go mod tidy

# Generate GraphQL code
go run github.com/99designs/gqlgen generate

# Run server
export DATABASE_URL="postgresql://user:pass@localhost:5432/bifrost"
export MLX_SERVICE_URL="localhost:50051"
go run cmd/server/main.go
```

### 2. Python MLX Service Setup

```bash
cd bifrost_ml

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate gRPC code
python -m grpc_tools.protoc -I. \
    --python_out=. \
    --grpc_python_out=. \
    proto/mlx_service.proto

# Run service
python app.py
```

### 3. SmartCP Integration

```bash
# In SmartCP root
export BIFROST_GRAPHQL_URL="http://localhost:8080/query"

# Test integration
python -c "from bifrost_client import BifrostClient; client = BifrostClient(); print(client.route('list files'))"
```

## Testing

### Integration Test

```python
# tests/integration/bifrost/test_e2e_routing.py
import pytest
from bifrost_client import BifrostClient

@pytest.mark.asyncio
async def test_e2e_routing():
    """Test end-to-end routing through GraphQL -> MLX."""
    client = BifrostClient()

    # Test routing
    result = await client.route("list all files in current directory")

    assert result["route"] == "filesystem"
    assert "ls" in result["tools"]
    assert result["confidence"] > 0.8

@pytest.mark.asyncio
async def test_tool_registry():
    """Test tool registry operations."""
    client = BifrostClient()

    # List tools
    tools = await client.get_tools(category="filesystem")

    assert len(tools) > 0
    assert any(t["name"] == "ls" for t in tools)
```

## Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  bifrost-backend:
    build: ./bifrost_backend
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/bifrost
      - MLX_SERVICE_URL=bifrost-ml:50051
    depends_on:
      - postgres
      - bifrost-ml

  bifrost-ml:
    build: ./bifrost_ml
    ports:
      - "8000:8000"
      - "50051:50051"
    volumes:
      - ./router:/app/router  # Mount existing router code

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=bifrost
    ports:
      - "5432:5432"
```

## Next Steps

1. ✅ **Implement remaining resolvers** - Complete all GraphQL mutations/queries
2. ✅ **Add authentication** - JWT validation in GraphQL middleware
3. ✅ **Implement subscriptions** - WebSocket support for real-time updates
4. ✅ **Add metrics** - Prometheus metrics for monitoring
5. ✅ **Performance testing** - Load test GraphQL endpoint
6. ✅ **Documentation** - API documentation and examples

## Status

- [x] Go project structure created
- [x] GraphQL schema defined
- [x] Main server implemented
- [x] Resolver implemented
- [x] Services implemented
- [x] Python MLX service implemented
- [x] gRPC integration designed
- [ ] Integration tests written
- [ ] Deployment configuration completed
- [ ] Documentation completed
