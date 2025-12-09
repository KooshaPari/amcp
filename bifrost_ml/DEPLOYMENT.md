# Bifrost ML Deployment Guide

## Quick Start

### 1. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Generate gRPC code
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/ml_service.proto

# Start service
python app.py

# Or use convenience script
./start.sh
```

Service available at:
- HTTP: http://localhost:8001
- gRPC: localhost:50051

### 2. Docker

```bash
# Build image
docker build -t bifrost-ml:latest .

# Run container
docker run -d \
  -p 8001:8001 \
  -p 50051:50051 \
  --name bifrost-ml \
  bifrost-ml:latest

# Check logs
docker logs -f bifrost-ml

# Health check
curl http://localhost:8001/health
```

### 3. Docker Compose

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

## Production Deployment

### Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:
```env
PORT=8001
GRPC_PORT=50051
LOG_LEVEL=INFO
DEFAULT_MODEL=claude-sonnet-4
OPTIMIZE_FOR=balanced
MAX_COST_PER_REQUEST_USD=0.10
DAILY_BUDGET_USD=100.0
MLX_DEVICE=gpu
```

### Kubernetes Deployment

```yaml
# bifrost-ml-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bifrost-ml
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bifrost-ml
  template:
    metadata:
      labels:
        app: bifrost-ml
    spec:
      containers:
      - name: bifrost-ml
        image: bifrost-ml:latest
        ports:
        - containerPort: 8001
          name: http
        - containerPort: 50051
          name: grpc
        env:
        - name: PORT
          value: "8001"
        - name: GRPC_PORT
          value: "50051"
        - name: LOG_LEVEL
          value: "INFO"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: bifrost-ml
spec:
  selector:
    app: bifrost-ml
  ports:
  - name: http
    port: 8001
    targetPort: 8001
  - name: grpc
    port: 50051
    targetPort: 50051
  type: ClusterIP
```

Deploy:
```bash
kubectl apply -f bifrost-ml-deployment.yaml
```

### Cloud Deployment

#### AWS ECS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t bifrost-ml:latest .
docker tag bifrost-ml:latest <account>.dkr.ecr.us-east-1.amazonaws.com/bifrost-ml:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/bifrost-ml:latest

# Create ECS task definition and service
```

#### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/<project>/bifrost-ml:latest

# Deploy to Cloud Run
gcloud run deploy bifrost-ml \
  --image gcr.io/<project>/bifrost-ml:latest \
  --platform managed \
  --port 8001 \
  --allow-unauthenticated \
  --region us-central1
```

#### Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Launch app
fly launch

# Deploy
fly deploy
```

## Monitoring

### Health Checks

```bash
# HTTP
curl http://localhost:8001/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### Prometheus Metrics (TODO)

Add to `app.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

Access metrics:
```bash
curl http://localhost:8001/metrics
```

### Logging

Logs are structured JSON:
```json
{
  "timestamp": "2025-12-03T00:00:00Z",
  "level": "INFO",
  "message": "Request processed",
  "duration_ms": 45,
  "endpoint": "/route",
  "model": "claude-sonnet-4"
}
```

## Load Balancing

### Nginx

```nginx
upstream bifrost_ml {
    least_conn;
    server bifrost-ml-1:8001;
    server bifrost-ml-2:8001;
    server bifrost-ml-3:8001;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://bifrost_ml;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /grpc {
        grpc_pass grpc://bifrost_ml;
    }
}
```

### HAProxy

```
backend bifrost_ml
    mode http
    balance roundrobin
    option httpchk GET /health
    server ml1 bifrost-ml-1:8001 check
    server ml2 bifrost-ml-2:8001 check
    server ml3 bifrost-ml-3:8001 check
```

## Performance Tuning

### Uvicorn Workers

```bash
# Multiple workers for better performance
uvicorn app:app \
  --host 0.0.0.0 \
  --port 8001 \
  --workers 4 \
  --loop uvloop
```

### Request Batching

For embeddings, batch requests:
```python
# Instead of multiple single requests
embed1 = await embed(["text1"])
embed2 = await embed(["text2"])

# Use single batch request
embeds = await embed(["text1", "text2"])
```

### Caching

Add Redis caching for frequently used embeddings:
```python
import aioredis

cache = await aioredis.from_url("redis://localhost")

async def get_cached_embedding(text):
    cached = await cache.get(f"embed:{text}")
    if cached:
        return json.loads(cached)

    embedding = await generate_embedding(text)
    await cache.setex(f"embed:{text}", 3600, json.dumps(embedding))
    return embedding
```

## Security

### API Authentication

Add API key validation:
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
```

### Rate Limiting

Add rate limiting:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/classify")
@limiter.limit("100/minute")
async def classify_prompt(request: ClassifyRequest):
    ...
```

## Troubleshooting

### Service won't start

1. Check if ports are available:
```bash
lsof -i :8001
lsof -i :50051
```

2. Check logs:
```bash
docker logs bifrost-ml
# or
journalctl -u bifrost-ml -f
```

3. Verify dependencies:
```bash
pip install -r requirements.txt
```

### High latency

1. Enable request logging:
```python
@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} {duration:.3f}s")
    return response
```

2. Check system resources:
```bash
docker stats bifrost-ml
```

3. Enable profiling:
```bash
pip install py-spy
py-spy record -o profile.svg -- python app.py
```

### Memory issues

1. Monitor memory usage:
```bash
docker stats --no-stream bifrost-ml
```

2. Adjust container limits:
```yaml
resources:
  limits:
    memory: "4Gi"
```

3. Use memory profiling:
```bash
pip install memory_profiler
python -m memory_profiler app.py
```

## Scaling

### Horizontal Scaling

```bash
# Kubernetes
kubectl scale deployment bifrost-ml --replicas=10

# Docker Swarm
docker service scale bifrost-ml=10

# Docker Compose
docker-compose up -d --scale bifrost-ml=10
```

### Vertical Scaling

Increase resources per instance:
```yaml
resources:
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

### Auto-scaling

Kubernetes HPA:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bifrost-ml-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bifrost-ml
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Backup and Recovery

### State Backup

No state to backup - service is stateless.

### Configuration Backup

```bash
# Backup environment
cp .env .env.backup

# Backup Kubernetes config
kubectl get all -n bifrost-ml -o yaml > bifrost-ml-backup.yaml
```

### Disaster Recovery

1. Rebuild from source:
```bash
git clone <repo>
cd bifrost_ml
docker build -t bifrost-ml:latest .
docker-compose up -d
```

2. Restore from image:
```bash
docker pull <registry>/bifrost-ml:latest
docker run -d -p 8001:8001 -p 50051:50051 <registry>/bifrost-ml:latest
```

## Updates

### Rolling Update

```bash
# Kubernetes
kubectl set image deployment/bifrost-ml bifrost-ml=bifrost-ml:v2

# Docker Compose
docker-compose pull
docker-compose up -d
```

### Blue-Green Deployment

1. Deploy new version:
```bash
kubectl apply -f bifrost-ml-v2-deployment.yaml
```

2. Switch traffic:
```bash
kubectl patch service bifrost-ml -p '{"spec":{"selector":{"version":"v2"}}}'
```

3. Remove old version:
```bash
kubectl delete deployment bifrost-ml-v1
```

## Support

For issues or questions:
- Check logs: `docker logs bifrost-ml`
- Health check: `curl http://localhost:8001/health`
- Test endpoints: `python test_service.py`
- GitHub Issues: <repo-url>
