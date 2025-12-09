# SmartCP Local Deployment - Quick Start

## 🚀 One-Command Deploy

```bash
# 1. Copy environment template
cp .env.local .env

# 2. (Optional) Add API keys to .env
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# VOYAGE_API_KEY=pa-...

# 3. Start everything
./scripts/start-local.sh
```

**Done!** All services running at:
- SmartCP MCP: http://localhost:8000
- Bifrost API: http://localhost:8001
- Bifrost GraphQL: http://localhost:8080/graphql
- Bifrost ML: http://localhost:8002

---

## ✅ Verify Deployment

```bash
# Check all services are healthy
./scripts/health-check.sh

# Run end-to-end tests
./scripts/test-deployment.sh
```

---

## 📊 View Logs

```bash
# All services
./scripts/logs.sh all

# Specific service
./scripts/logs.sh smartcp
./scripts/logs.sh bifrost-api
./scripts/logs.sh postgres
```

---

## 🛑 Stop Services

```bash
# Stop (keeps data)
./scripts/stop-local.sh

# Stop and remove all data
docker-compose -f docker-compose.local.yml down -v
```

---

## 🔧 Troubleshooting

### Services won't start?

```bash
# Check Docker is running
docker info

# Check ports aren't in use
lsof -i :8000 :8001 :8080 :5432

# Clean and restart
docker-compose -f docker-compose.local.yml down -v
./scripts/start-local.sh
```

### Service unhealthy?

```bash
# Check logs for errors
./scripts/logs.sh smartcp --tail=100

# Restart specific service
docker-compose -f docker-compose.local.yml restart smartcp
```

---

## 📚 Full Documentation

See [LOCAL_DEPLOYMENT.md](./LOCAL_DEPLOYMENT.md) for:
- Detailed architecture
- Configuration options
- Development workflow
- Advanced troubleshooting
- API documentation links

---

## 🎯 What's Running?

| Service | Port | Purpose |
|---------|------|---------|
| SmartCP | 8000 | FastMCP server with tools |
| Bifrost API | 8001 | HTTP API (FastAPI) |
| Bifrost Backend | 8080 | GraphQL + gRPC |
| Bifrost ML | 8002 | ML inference (MLX) |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache + queues |
| Qdrant | 6333 | Vector database |

---

## 🧪 Test APIs

```bash
# SmartCP health
curl http://localhost:8000/health

# List MCP tools
curl http://localhost:8000/tools

# Bifrost API docs
open http://localhost:8001/docs

# GraphQL playground
open http://localhost:8080/graphql

# ML service health
curl http://localhost:8002/health
```

---

## 📦 What Gets Installed?

- **7 Docker containers** (services + infrastructure)
- **4 Docker volumes** (persistent data)
- **1 Docker network** (inter-service communication)

Total: ~2-3 GB disk space (first time)

---

## ⚡ Quick Commands Reference

```bash
# Start
./scripts/start-local.sh

# Stop
./scripts/stop-local.sh

# Logs
./scripts/logs.sh [service]

# Health
./scripts/health-check.sh

# Test
./scripts/test-deployment.sh

# Clean everything
docker-compose -f docker-compose.local.yml down -v --rmi all
```

---

**Need help?** Check [LOCAL_DEPLOYMENT.md](./LOCAL_DEPLOYMENT.md) or [CLAUDE.md](./CLAUDE.md)
