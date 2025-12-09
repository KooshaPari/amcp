# SmartCP Local Deployment Guide (Updated for Hybrid Default)

This guide reflects the corrected architecture: SmartCP is stateless and delegates to Bifrost; Supabase Cloud (pgvector) is the default datastore; local Postgres/Redis are optional profiles; Qdrant is not part of the default stack.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [Running Services](#running-services)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Development Workflow](#development-workflow)
- [Cleanup](#cleanup)

---

## Quick Start (Hybrid default)

```bash
# 1) Create env
cp .env.local .env

# Required: Supabase cloud creds (for auth/pgvector)
echo "SUPABASE_URL=https://<project>.supabase.co" >> .env
echo "SUPABASE_KEY=<anon-or-service-key>" >> .env

# Optional: Bifrost API key
echo "BIFROST_API_KEY=<optional>" >> .env

# 2) Run SmartCP + Bifrost only (cloud data)
docker compose -f smartcp/docker-compose.local.yml up -d smartcp bifrost-api bifrost-backend

# 3) (Optional) add local Postgres/Redis for latency/offline
docker compose -f smartcp/docker-compose.local.yml --profile local-postgres --profile local-redis up -d
```

Endpoints:
- SmartCP MCP HTTP: http://localhost:8000
- Bifrost GraphQL: http://localhost:8080/graphql (via bifrost-backend)
- Bifrost API facade: http://localhost:8001

Note: Any Qdrant or mandatory-local-Postgres references elsewhere in this file are legacy and should be ignored unless you intentionally add a custom adapter; default vector store is Supabase pgvector (cloud) with optional local Postgres+pgvectorscale.

---

## Prerequisites

### Required Software

1. **Docker Desktop** (v20.10+)
   - Download: https://www.docker.com/products/docker-desktop
   - Includes Docker Compose
   - Make sure Docker daemon is running

2. **Git** (for cloning)
   ```bash
   git --version  # Should be v2.0+
   ```

3. **Bash** (for scripts)
   - macOS/Linux: Built-in
   - Windows: Use Git Bash or WSL2

### System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **CPU**: Multi-core recommended for parallel services
- **OS**: macOS, Linux, or Windows 10+ with WSL2

### Optional (for development)

- **Python 3.12+** (for local development outside Docker)
- **Go 1.21+** (for Bifrost backend development)
- **Node.js 18+** (for frontend if needed)

---

## Architecture Overview

### Services (updated)

```
┌───────────────────────────────────────────────┐
│ SmartCP (stateless MCP)  : 8000               │
│ Bifrost API (FastAPI)    : 8001               │
│ Bifrost Backend (GraphQL): 8080 (9090 gRPC)   │
│ Bifrost ML (optional)    : 8002               │
├───────────────────────────────────────────────┤
│ Cloud-first data (default)                    │
│   Supabase Postgres + pgvector (cloud)        │
│   Redis/NATS/Neo4j cloud (optional)           │
│ Local optional (profiles)                     │
│   Postgres + pgvectorscale (profile: local-postgres) │
│   Redis (profile: local-redis)                │
└───────────────────────────────────────────────┘
```

### Component Descriptions

| Service | Technology | Purpose | Port |
|---------|-----------|---------|------|
| **smartcp** | Python + FastMCP | MCP server with tools | 8000 |
| **bifrost-api** | Python + FastAPI | HTTP API for Bifrost | 8001 |
| **bifrost-backend** | Go + GraphQL | GraphQL backend + gRPC | 8080/9090 |
| **bifrost-ml** | Python + MLX | ML inference service | 8002 |
| **postgres** | PostgreSQL 16 | Optional local DB (profile: local-postgres) | 5432 |
| **redis** | Redis 7 | Optional local cache (profile: local-redis) | 6379 |
| **qdrant** | — | Not used (removed from default stack) | — |

---

## Configuration

### Environment Variables

1. **Copy the template:**
   ```bash
   cp .env.local .env
   ```

2. **Add your API keys** (in `.env`):
   ```bash
   # Required for full functionality
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   VOYAGE_API_KEY=pa-...

   # Optional for Google services
   GOOGLE_PROJECT_ID=your-project
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
   ```

3. **Customize if needed:**
   ```bash
   # Change ports if there are conflicts
   SMARTCP_PORT=8000
   BIFROST_API_PORT=8001
   BIFROST_BACKEND_PORT=8080

   # Adjust log level
   LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR

   # Enable/disable features
   ENABLE_CACHING=true
   RATE_LIMIT=100
   ```

### Database Configuration

The PostgreSQL database is automatically initialized with:

- **Database**: `smartcp`
- **User**: `smartcp_user`
- **Password**: `smartcp_dev_password` (dev only!)
- **Migrations**: Run automatically on startup

**Custom database settings:**
```bash
# In .env
DATABASE_URL=postgresql://custom_user:custom_pass@localhost:5432/custom_db
```

---

## Running Services

### Start Everything

```bash
./scripts/start-local.sh
```

**What it does:**
1. Checks prerequisites (Docker, Docker Compose)
2. Loads environment variables
3. Builds Docker images (first time only)
4. Starts all services
5. Waits for health checks
6. Displays service URLs

**Expected output:**
```
========================================
SmartCP Local Deployment Startup
========================================

[1/5] Checking prerequisites...
✓ Docker and Docker Compose are available

[2/5] Loading environment variables...
✓ Environment variables loaded from .env.local

[3/5] Checking API keys...
✓ All required API keys present

[4/5] Building and starting services...
Creating network "smartcp-local" ...
Creating smartcp-postgres ... done
Creating smartcp-redis    ... done
Creating smartcp-qdrant   ... done
Creating smartcp-mcp      ... done
Creating smartcp-bifrost-api ... done
Creating smartcp-bifrost-backend ... done
Creating smartcp-bifrost-ml ... done

[5/5] Waiting for services to be healthy...
Services ready: 6/6 (waited 30s)
✓ All services are healthy!

========================================
Services Started Successfully!
========================================

Service URLs:
  SmartCP MCP Server:    http://localhost:8000
  Bifrost HTTP API:      http://localhost:8001
  Bifrost GraphQL:       http://localhost:8080/graphql
  Bifrost ML Service:    http://localhost:8002
```

### View Logs

```bash
# All services
./scripts/logs.sh all

# Specific service
./scripts/logs.sh smartcp
./scripts/logs.sh bifrost-api
./scripts/logs.sh bifrost-backend
./scripts/logs.sh bifrost-ml
./scripts/logs.sh postgres

# Last 100 lines
./scripts/logs.sh smartcp --tail=100

# Stop following
# Press Ctrl+C
```

### Check Health

```bash
./scripts/health-check.sh
```

**Expected output:**
```
========================================
SmartCP Service Health Check
========================================

HTTP Services:
Checking SmartCP MCP Server... ✓ Healthy
Checking Bifrost HTTP API... ✓ Healthy
Checking Bifrost GraphQL... ✓ Healthy
Checking Bifrost ML Service... ✓ Healthy

Infrastructure Services:
Checking PostgreSQL... ✓ Reachable
Checking Redis... ✓ Reachable

Container Status:
NAME                    STATUS              PORTS
smartcp-postgres        Up 2 minutes       5432/tcp
smartcp-redis           Up 2 minutes       6379/tcp
smartcp-mcp             Up 2 minutes       8000/tcp
smartcp-bifrost-api     Up 2 minutes       8001/tcp
smartcp-bifrost-backend Up 2 minutes       8080/tcp, 9090/tcp
smartcp-bifrost-ml      Up 2 minutes       8002/tcp

========================================
All services are healthy! ✓
========================================
```

### Stop Services

```bash
# Stop all services (keeps data)
./scripts/stop-local.sh

# Stop and remove volumes (fresh start)
docker-compose -f docker-compose.local.yml down -v
```

---

## Testing

### Test Each Service

1. **SmartCP MCP Server** (http://localhost:8000)
   ```bash
   # Health check
   curl http://localhost:8000/health

   # List tools
   curl http://localhost:8000/tools
   ```

2. **Bifrost HTTP API** (http://localhost:8001)
   ```bash
   # Health check
   curl http://localhost:8001/health

   # API docs
   open http://localhost:8001/docs
   ```

3. **Bifrost GraphQL** (http://localhost:8080)
   ```bash
   # Health check
   curl http://localhost:8080/health

   # GraphQL Playground
   open http://localhost:8080/graphql
   ```

4. **Bifrost ML Service** (http://localhost:8002)
   ```bash
   # Health check
   curl http://localhost:8002/health

   # Model info
   curl http://localhost:8002/models
   ```

### End-to-End Test

```bash
# From project root
cd /Users/kooshapari/temp-PRODVERCEL/485/API/smartcp

# Run tests (if venv exists)
source .venv/bin/activate
pytest tests/integration/ -v

# Or via Docker
docker-compose -f docker-compose.local.yml exec smartcp pytest tests/
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.local.yml exec postgres \
  psql -U smartcp_user -d smartcp

# Run query
docker-compose -f docker-compose.local.yml exec postgres \
  psql -U smartcp_user -d smartcp -c "SELECT * FROM users LIMIT 10;"

# Connect with psql (if installed locally)
psql postgresql://smartcp_user:smartcp_dev_password@localhost:5432/smartcp
```

### Redis CLI

```bash
# Connect to Redis
docker-compose -f docker-compose.local.yml exec redis redis-cli

# Check keys
docker-compose -f docker-compose.local.yml exec redis redis-cli KEYS "*"
```

## Troubleshooting

### Services Won't Start

**Check Docker:**
```bash
# Is Docker running?
docker info

# Check Docker version
docker --version
docker-compose --version
```

**Check ports:**
```bash
# Are ports already in use?
lsof -i :8000  # SmartCP
lsof -i :8001  # Bifrost API
lsof -i :8080  # Bifrost Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill process on port (if needed)
kill -9 <PID>
```

**Check disk space:**
```bash
df -h
docker system df
```

### Service Unhealthy

**Check logs:**
```bash
# View service logs
./scripts/logs.sh smartcp --tail=100

# Check for errors
./scripts/logs.sh smartcp | grep -i error
```

**Restart specific service:**
```bash
docker-compose -f docker-compose.local.yml restart smartcp
```

**Rebuild service:**
```bash
docker-compose -f docker-compose.local.yml up -d --build smartcp
```

### Database Connection Errors

**Check PostgreSQL:**
```bash
# Is Postgres running?
docker-compose -f docker-compose.local.yml ps postgres

# Check Postgres logs
./scripts/logs.sh postgres --tail=50

# Test connection
docker-compose -f docker-compose.local.yml exec postgres \
  pg_isready -U smartcp_user
```

**Reset database:**
```bash
# Stop services
./scripts/stop-local.sh

# Remove volumes
docker-compose -f docker-compose.local.yml down -v

# Start fresh
./scripts/start-local.sh
```

### Redis Connection Errors

```bash
# Check Redis
docker-compose -f docker-compose.local.yml exec redis redis-cli ping

# Should return: PONG
```

### Slow Performance

**Check resource usage:**
```bash
# Container stats
docker stats

# System resources
docker system df
```

**Increase Docker resources:**
1. Open Docker Desktop
2. Settings → Resources
3. Increase:
   - CPUs: 4+
   - Memory: 8GB+
   - Disk: 10GB+

### Port Conflicts

**Change ports in `.env`:**
```bash
SMARTCP_PORT=8010
BIFROST_API_PORT=8011
BIFROST_BACKEND_PORT=8020
```

**Restart services:**
```bash
./scripts/stop-local.sh
./scripts/start-local.sh
```

### Build Failures

**Clean Docker cache:**
```bash
# Remove all containers and images
docker-compose -f docker-compose.local.yml down --rmi all

# Prune system
docker system prune -a

# Rebuild from scratch
./scripts/start-local.sh
```

### API Key Errors

**Check keys are set:**
```bash
# View current environment (sanitized)
docker-compose -f docker-compose.local.yml exec smartcp env | grep API_KEY

# Add keys to .env
echo "OPENAI_API_KEY=sk-..." >> .env

# Restart to pick up new keys
docker-compose -f docker-compose.local.yml restart
```

---

## Development Workflow

### Making Code Changes

**Changes are live-mounted (no rebuild needed for Python):**

```bash
# Edit code
vim bifrost_api/routes.py

# Logs show changes
./scripts/logs.sh bifrost-api

# Or restart service
docker-compose -f docker-compose.local.yml restart bifrost-api
```

**Go services require rebuild:**
```bash
# Edit Go code
vim bifrost_backend/internal/handlers/graphql.go

# Rebuild and restart
docker-compose -f docker-compose.local.yml up -d --build bifrost-backend
```

### Running Tests Inside Containers

```bash
# SmartCP tests
docker-compose -f docker-compose.local.yml exec smartcp pytest tests/

# With coverage
docker-compose -f docker-compose.local.yml exec smartcp \
  pytest tests/ --cov=. --cov-report=html
```

### Debugging

**Attach to container:**
```bash
# Interactive shell
docker-compose -f docker-compose.local.yml exec smartcp bash

# Python debugger
docker-compose -f docker-compose.local.yml exec smartcp python -m pdb main.py

# View environment
docker-compose -f docker-compose.local.yml exec smartcp env
```

**Enable debug logging:**
```bash
# In .env
LOG_LEVEL=DEBUG

# Restart
docker-compose -f docker-compose.local.yml restart
```

### Database Migrations

**Run new migration:**
```bash
# Create migration file
cat > migrations/000004_new_feature.up.sql << EOF
-- Your migration here
CREATE TABLE new_table (...);
EOF

# Restart Postgres (auto-runs migrations)
docker-compose -f docker-compose.local.yml restart postgres

# Or run manually
docker-compose -f docker-compose.local.yml exec postgres \
  psql -U smartcp_user -d smartcp -f /docker-entrypoint-initdb.d/000004_new_feature.up.sql
```

---

## Cleanup

### Remove All Services

```bash
# Stop and remove containers
./scripts/stop-local.sh

# Remove volumes (data)
docker-compose -f docker-compose.local.yml down -v

# Remove images
docker-compose -f docker-compose.local.yml down --rmi all
```

### Clean Docker System

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup (WARNING: affects all Docker resources)
docker system prune -a --volumes
```

### Reset to Fresh State

```bash
# 1. Stop everything
./scripts/stop-local.sh

# 2. Remove volumes
docker-compose -f docker-compose.local.yml down -v

# 3. Remove images
docker-compose -f docker-compose.local.yml down --rmi all

# 4. Start fresh
./scripts/start-local.sh
```

---

## Common Issues and Solutions

### Issue: "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker Desktop
open -a Docker

# Wait for Docker to start
docker info
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in .env
SMARTCP_PORT=8010
```

### Issue: "Service unhealthy after 2 minutes"

**Solution:**
```bash
# Check logs for errors
./scripts/logs.sh smartcp --tail=100

# Common causes:
# - Missing API keys
# - Database not ready
# - Wrong configuration

# Try restart
docker-compose -f docker-compose.local.yml restart smartcp
```

### Issue: "Database connection refused"

**Solution:**
```bash
# Check if Postgres is ready
docker-compose -f docker-compose.local.yml exec postgres pg_isready

# Wait for Postgres health check
./scripts/health-check.sh

# If still failing, restart
docker-compose -f docker-compose.local.yml restart postgres
docker-compose -f docker-compose.local.yml restart smartcp
```

### Issue: "Out of disk space"

**Solution:**
```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a --volumes

# Free up space
rm -rf ~/.docker/logs/*
```

---

## Additional Resources

### Documentation

- [SmartCP README](./README.md)
- [Bifrost API Docs](./bifrost_api/README.md)
- [Bifrost Backend Docs](./bifrost_backend/README.md)
- [CLAUDE.md](./CLAUDE.md) - Development guide

### API Documentation

- **SmartCP**: http://localhost:8000/docs
- **Bifrost HTTP API**: http://localhost:8001/docs
- **Bifrost GraphQL**: http://localhost:8080/graphql

### Monitoring

- **Docker Dashboard**: Docker Desktop → Containers
_- Qdrant dashboard and references removed (not part of default stack)._
- **Container Stats**: `docker stats`
- **Service Logs**: `./scripts/logs.sh [service]`

### Getting Help

1. **Check logs**: `./scripts/logs.sh [service]`
2. **Health check**: `./scripts/health-check.sh`
3. **Search issues**: GitHub Issues
4. **Documentation**: This file + README.md

---

## Success Criteria

Your local deployment is working when:

- ✅ All services show as "Healthy" in health check
- ✅ You can access all service URLs
- ✅ Database queries work
- ✅ API endpoints respond
- ✅ No errors in logs
- ✅ End-to-end tests pass

**Quick verification:**
```bash
./scripts/health-check.sh && \
curl http://localhost:8000/health && \
curl http://localhost:8001/health && \
curl http://localhost:8080/health && \
echo "✓ All systems operational!"
```

---

## Next Steps

After successful local deployment:

1. **Explore the APIs**: Visit http://localhost:8001/docs
2. **Run tests**: `docker-compose exec smartcp pytest tests/`
3. **Make changes**: Edit code and see live updates
4. **Read docs**: Check component-specific READMEs
5. **Deploy to staging**: See DEPLOYMENT.md (when ready)

**Happy developing!** 🚀
