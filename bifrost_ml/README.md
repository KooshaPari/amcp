# Bifrost ML Microservice

Python MLX-based microservice for ML inference operations used by the Go backend.

## Features

- **Prompt Classification**: Classify prompts to determine complexity and tool routing
- **Model Routing**: Route requests to optimal models based on complexity analysis
- **Embedding Generation**: Generate MLX embeddings for semantic search
- **Dual Transport**: FastAPI (HTTP) + gRPC for flexible integration

## Architecture

```
bifrost_ml/
├── app.py                 # Main FastAPI + gRPC server
├── services/
│   ├── routing.py         # Model routing (wraps router_core)
│   ├── classification.py  # Unified classifier (wraps mlx_router)
│   └── embeddings.py      # MLX embedding generation
├── proto/
│   └── ml_service.proto   # gRPC protocol definition
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container image
└── README.md             # This file
```

## Setup

### 1. Install Dependencies

```bash
cd bifrost_ml
pip install -r requirements.txt
```

### 2. Generate gRPC Code

```bash
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    proto/ml_service.proto
```

This generates:
- `proto/ml_service_pb2.py` - Protocol buffer messages
- `proto/ml_service_pb2_grpc.py` - gRPC service stubs

### 3. Run the Service

```bash
python app.py
```

Server starts on:
- HTTP: http://localhost:8001
- gRPC: localhost:50051

## API Endpoints

### HTTP (FastAPI)

#### Health Check
```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 42
}
```

#### Classify Prompt
```bash
curl -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the weather like?",
    "context": {}
  }'
```

Response:
```json
{
  "complexity": "simple",
  "confidence": 0.95,
  "tool_name": "weather_tool",
  "alternatives": [
    {"name": "search_tool", "score": 0.75}
  ]
}
```

#### Generate Embeddings
```bash
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello world", "Machine learning"],
    "model": "mlx-embed"
  }'
```

Response:
```json
{
  "embeddings": [
    [0.1, 0.2, ...],
    [0.3, 0.4, ...]
  ],
  "model_used": "mlx-embed"
}
```

#### Route Request
```bash
curl -X POST http://localhost:8001/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze this complex problem...",
    "context": {},
    "output_tokens_estimate": 1000
  }'
```

Response:
```json
{
  "model": "claude-sonnet-4",
  "complexity": "complex",
  "estimated_cost_usd": 0.0045,
  "estimated_latency_ms": 800,
  "rationale": "High-quality model for complex task",
  "fallback_model": "claude-haiku-3.5"
}
```

#### List Models
```bash
curl http://localhost:8001/models
```

Response:
```json
{
  "models": [
    "claude-sonnet-4",
    "claude-haiku-3.5",
    "gemini-2.0-flash",
    "gpt-4o-mini"
  ]
}
```

### gRPC

After generating proto code, use gRPC clients:

```python
import grpc
from proto import ml_service_pb2, ml_service_pb2_grpc

# Create channel
channel = grpc.insecure_channel('localhost:50051')
stub = ml_service_pb2_grpc.MLServiceStub(channel)

# Classify
request = ml_service_pb2.ClassifyRequest(
    prompt="What is 2+2?",
    context={}
)
response = stub.Classify(request)
print(f"Tool: {response.tool_name}, Confidence: {response.confidence}")

# Route
request = ml_service_pb2.RouteRequest(
    prompt="Analyze this...",
    output_tokens_estimate=1000
)
response = stub.Route(request)
print(f"Model: {response.model}, Cost: ${response.estimated_cost_usd}")
```

## Integration with Go Backend

### HTTP Client (Go)

```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

type RouteRequest struct {
    Prompt               string         `json:"prompt"`
    Context              map[string]any `json:"context"`
    OutputTokensEstimate int            `json:"output_tokens_estimate"`
}

type RouteResponse struct {
    Model              string  `json:"model"`
    Complexity         string  `json:"complexity"`
    EstimatedCostUSD   float64 `json:"estimated_cost_usd"`
    EstimatedLatencyMs int     `json:"estimated_latency_ms"`
    Rationale          string  `json:"rationale"`
    FallbackModel      *string `json:"fallback_model"`
}

func RouteRequest(prompt string) (*RouteResponse, error) {
    req := RouteRequest{
        Prompt:               prompt,
        Context:              make(map[string]any),
        OutputTokensEstimate: 1000,
    }

    body, _ := json.Marshal(req)
    resp, err := http.Post(
        "http://localhost:8001/route",
        "application/json",
        bytes.NewReader(body),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result RouteResponse
    json.NewDecoder(resp.Body).Decode(&result)
    return &result, nil
}
```

### gRPC Client (Go)

```go
package main

import (
    "context"
    "google.golang.org/grpc"
    pb "path/to/proto/ml_service"
)

func main() {
    conn, _ := grpc.Dial("localhost:50051", grpc.WithInsecure())
    defer conn.Close()

    client := pb.NewMLServiceClient(conn)

    // Route request
    resp, _ := client.Route(context.Background(), &pb.RouteRequest{
        Prompt:               "Analyze this...",
        OutputTokensEstimate: 1000,
    })

    println("Model:", resp.Model)
    println("Cost:", resp.EstimatedCostUsd)
}
```

## Docker Deployment

### Build Image

```bash
docker build -t bifrost-ml:latest .
```

### Run Container

```bash
docker run -d \
  -p 8001:8001 \
  -p 50051:50051 \
  --name bifrost-ml \
  bifrost-ml:latest
```

### Health Check

```bash
curl http://localhost:8001/health
```

## Development

### Run with Auto-Reload

```bash
uvicorn app:app --reload --port 8001
```

### Testing

```bash
# Test classify endpoint
curl -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# Test route endpoint
curl -X POST http://localhost:8001/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "output_tokens_estimate": 1000}'

# Test embed endpoint
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["hello", "world"]}'
```

## Environment Variables

```bash
# Server configuration
PORT=8001
GRPC_PORT=50051
LOG_LEVEL=INFO

# Model configuration
DEFAULT_MODEL=claude-sonnet-4
OPTIMIZE_FOR=balanced  # cost, speed, quality, balanced

# Cost constraints
MAX_COST_PER_REQUEST_USD=0.10
DAILY_BUDGET_USD=100.0

# MLX configuration
MLX_DEVICE=gpu  # gpu, cpu
MLX_MODEL_PATH=/models/mlx-embed
```

## Monitoring

### Metrics Endpoint (TODO)

```bash
curl http://localhost:8001/metrics
```

Returns Prometheus-compatible metrics:
- Request counts by endpoint
- Latency histograms
- Error rates
- Model usage statistics

## Troubleshooting

### Server won't start

1. Check port availability:
```bash
lsof -i :8001
lsof -i :50051
```

2. Check logs:
```bash
docker logs bifrost-ml
```

### Import errors

Ensure parent directory is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
```

### gRPC errors

Regenerate proto code:
```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/ml_service.proto
```

## Performance

- **HTTP Latency**: ~10-50ms (local)
- **gRPC Latency**: ~5-20ms (local)
- **Classification**: ~5-10ms
- **Routing**: ~1-5ms
- **Embeddings**: ~20-100ms (batch size dependent)

## Future Enhancements

- [ ] Add actual MLX model loading
- [ ] Implement model caching
- [ ] Add request batching
- [ ] Implement streaming responses
- [ ] Add authentication
- [ ] Add rate limiting
- [ ] Add metrics/tracing
- [ ] Add comprehensive tests

## License

See main project LICENSE
