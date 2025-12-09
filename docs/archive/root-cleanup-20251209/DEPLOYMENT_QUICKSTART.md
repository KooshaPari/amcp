# SmartCP Local Deployment - Quick Start

## 🚀 One-Command Deploy

```bash
# 1. Copy environment template
cp .env.local .env

# 2. (Optional) Add API keys to .env
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# VOYAGE_API_KEY=pa-...

# 3. Start everything (default = cloud Supabase/Redis/NATS/Neo4j; no Docker)
# Use your IaC to install services natively or run:
#   systemd/launchd/services placed by IaC
# For quick local (Linux/macOS) without Docker:
#   make dev-up   # builds Go backend + starts smartcp/bifrost-api locally
# (Windows: use the native installer path below)
```

**Done!** All services running natively (no Docker):
- SmartCP MCP: http://localhost:8000
- Bifrost API: http://localhost:8001
- Bifrost GraphQL: http://localhost:8080/graphql
- Bifrost ML: http://localhost:8002 (only if provisioned)

---

## ✅ Verify Deployment

```bash
# Check all services are healthy
# (replace with your IaC health commands or curl checks)
curl -f http://localhost:8000/health
curl -f http://localhost:8080/health

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
Use your service manager (systemd/launchd/Windows services) to stop/start.
Docker and docker-compose are no longer supported.
```

---

## 🔧 Troubleshooting

### Services won't start?

```bash
Ensure services are installed/enabled by your IaC and ports are free:
`lsof -i :8000 :8001 :8080 :5432`
```

### Service unhealthy?

```bash
# Check logs for errors
./scripts/logs.sh smartcp --tail=100

Restart via your service manager (systemctl/launchctl/win_service).
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
| PostgreSQL | 5432 | Primary database (only if enabled locally) |
| Redis | 6379 | Cache + queues (only if enabled locally) |
| NATS | 4222 | Message bus (cloud by default, local only if enabled) |
| Neo4j | 7687 | Graph DB (cloud by default, local only if enabled) |

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

Docker footprint: none (all native services).

Total: ~2-3 GB disk space (first time)

---

## ⚡ Quick Commands Reference

```bash
# Start
./scripts/start-local.sh

Stop/Start/Logs/Health/Test
- Use your platform service manager (systemctl/launchctl/WinSvc).
- Logs: /var/log/smartcp/*.log (Linux/macOS) or ProgramData\SmartCP\logs (Windows).
- Health: curl http://localhost:8000/health and http://localhost:8080/health.
- Tests: run your CI/IaC-driven contract tests against native services.
```

---

**Need help?** Check [LOCAL_DEPLOYMENT.md](./LOCAL_DEPLOYMENT.md) or [CLAUDE.md](./CLAUDE.md)
