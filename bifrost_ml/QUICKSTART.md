# Bifrost ML Quick Start

## 60 Second Start

```bash
cd bifrost_ml

# Install dependencies (if not already)
pip install -r requirements.txt

# Start service
./start.sh
```

Server ready at http://localhost:8001

## Test It

```bash
# Health check
curl http://localhost:8001/health

# Route a request
curl -X POST http://localhost:8001/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze this complex problem", "output_tokens_estimate": 1000}'
```

## Docker Start

```bash
# One command deployment
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Go Integration

```go
// Copy from examples/go_client.go
import "bytes"
import "encoding/json"
import "net/http"

func RouteRequest(prompt string) (*RouteResponse, error) {
    req := RouteRequest{Prompt: prompt, OutputTokensEstimate: 1000}
    body, _ := json.Marshal(req)
    resp, _ := http.Post("http://localhost:8001/route",
                         "application/json",
                         bytes.NewReader(body))
    var result RouteResponse
    json.NewDecoder(resp.Body).Decode(&result)
    return &result, nil
}
```

## All Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/classify` | POST | Classify prompt |
| `/embed` | POST | Generate embeddings |
| `/route` | POST | Route to model |
| `/models` | GET | List models |

## Full Documentation

- [README.md](README.md) - Complete guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment options
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details

## Need Help?

```bash
# Run test suite
python test_service.py

# Check logs
docker logs bifrost-ml

# Verify imports
python -c "import app; print('OK')"
```
