# SmartCP Local Deployment Guide

**Date:** December 2, 2025
**Status:** IMPLEMENTATION REQUIRED
**Version:** 1.0.0 (Planned)

---

## ⚠️ IMPORTANT NOTICE

**This guide describes the INTENDED local deployment process. Currently, the Go backend services are NOT IMPLEMENTED.**

**Current Status:**
- ✅ Python SDKs (Bifrost, SmartCP) - READY
- ✅ Docker Compose configuration - READY
- ✅ Database schema design - READY
- ❌ Go GraphQL backend - NOT IMPLEMENTED
- ❌ Database migrations - NOT EXECUTED
- ❌ Service orchestration - NOT VALIDATED

**See `GAPS_ANALYSIS.md` for complete gap inventory.**

---

## Prerequisites

### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| **Docker Desktop** | 24.0+ | Container runtime | [Download](https://www.docker.com/products/docker-desktop) |
| **Docker Compose** | 2.20+ | Service orchestration | Included with Docker Desktop |
| **Go** | 1.21+ | Go backend compilation | [Download](https://go.dev/dl/) |
| **Python** | 3.10+ | Python services | [Download](https://python.org) |
| **PostgreSQL Client** | 15+ | Database access (optional) | `brew install postgresql` |
| **Git** | 2.40+ | Version control | [Download](https://git-scm.com) |

### System Requirements

- **CPU:** 4+ cores recommended
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 20GB free space
- **OS:** macOS 12+, Ubuntu 22.04+, Windows 11+

---

## Step 1: Clone and Setup

### 1.1 Clone Repository

```bash
# Clone the repository
git clone https://github.com/smartcp/api.git
cd api/smartcp

# Verify you're in the right directory
ls -la
# Should see: docker-compose.yml, requirements.txt, bifrost_backend/, router/, etc.
```

### 1.2 Environment Setup

```bash
# Create virtual environment (Python)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import fastmcp; print('Python dependencies OK')"
```

### 1.3 Go Dependencies

```bash
cd bifrost_backend

# Initialize Go modules
go mod tidy

# Install gqlgen (GraphQL code generator)
go install github.com/99designs/gqlgen@latest

# Verify installation
go version
# Should output: go version go1.21+ ...

cd ..
```

---

## Step 2: Environment Configuration

### 2.1 Create Environment File

Create `.env.local` in the project root:

```bash
cat > .env.local << 'EOF'
# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smartcp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=smartcp

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

# Bifrost Go Backend
BIFROST_BACKEND_URL=http://localhost:8080
BIFROST_BACKEND_PORT=8080

# SmartCP Python API
SMARTCP_API_URL=http://localhost:8000
SMARTCP_API_PORT=8000

# Bifrost Python HTTP API
BIFROST_HTTP_API_URL=http://localhost:8001
BIFROST_HTTP_API_PORT=8001

# ============================================================================
# API KEYS & SECRETS
# ============================================================================

# OpenAI API (for embeddings/routing)
OPENAI_API_KEY=your_openai_key_here

# Voyage AI (for embeddings)
VOYAGE_API_KEY=your_voyage_key_here

# Supabase (for persistence layer)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# ============================================================================
# DEVELOPMENT FLAGS
# ============================================================================

# Logging
LOG_LEVEL=INFO
ENABLE_DEBUG_LOGGING=false

# Caching
ENABLE_CACHING=true
CACHE_TTL=300

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# ============================================================================
# SECURITY
# ============================================================================

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET=your_jwt_secret_here

# API Key for protected endpoints
API_KEY=your_api_key_here

EOF
```

### 2.2 Generate Secrets

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate API key
openssl rand -hex 32

# Update .env.local with generated values
```

### 2.3 Environment Validation

```bash
# Validate environment file
if [ -f .env.local ]; then
    echo "✅ Environment file exists"
    source .env.local

    # Check required variables
    required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "NEO4J_URI"
        "OPENAI_API_KEY"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Missing required variable: $var"
        else
            echo "✅ $var is set"
        fi
    done
else
    echo "❌ .env.local not found"
    exit 1
fi
```

---

## Step 3: Database Setup

### 3.1 Create PostgreSQL Database

```bash
# Start PostgreSQL service
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready -U postgres

# Create database
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE smartcp;"

# Verify database
docker-compose exec postgres psql -U postgres -l | grep smartcp
```

### 3.2 Run Database Migrations

**⚠️ BLOCKED:** Migrations not yet created. See `GAPS_ANALYSIS.md` Gap 2.

```bash
# ❌ NOT IMPLEMENTED YET
# cd bifrost_backend
# go run cmd/migrate/main.go up
```

**Manual Workaround (Temporary):**

```bash
# Create tables manually for testing
docker-compose exec postgres psql -U postgres -d smartcp << 'EOF'
-- Tools table
CREATE TABLE IF NOT EXISTS tools (
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
CREATE TABLE IF NOT EXISTS routes_cache (
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
CREATE TABLE IF NOT EXISTS executions (
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

-- Indexes
CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_status ON tools(status);
CREATE INDEX idx_routes_cache_expires ON routes_cache(expires_at);
CREATE INDEX idx_executions_tool_id ON executions(tool_id);
CREATE INDEX idx_executions_status ON executions(status);

EOF

# Verify tables created
docker-compose exec postgres psql -U postgres -d smartcp -c "\dt"
```

### 3.3 Neo4j Setup

```bash
# Start Neo4j
docker-compose up -d neo4j

# Wait for Neo4j to be ready
sleep 30

# Verify Neo4j
curl -u neo4j:password http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"RETURN 1"}]}'

# Should return: {"results":[{"columns":["1"],"data":[{"row":[1]}]}]}
```

### 3.4 Redis Setup

```bash
# Start Redis
docker-compose up -d redis

# Verify Redis
docker-compose exec redis redis-cli ping
# Should return: PONG
```

---

## Step 4: Build Services

### 4.1 Build Go Backend

**⚠️ BLOCKED:** Go backend not implemented. See `GAPS_ANALYSIS.md` Gap 1.

```bash
# ❌ NOT IMPLEMENTED YET
# cd bifrost_backend
# go build -o bin/server cmd/server/main.go
```

**Temporary Workaround:**

```bash
# Skip Go backend for now
echo "⚠️  Go backend not implemented. Skipping."
```

### 4.2 Build Python Services

```bash
# Verify Python services are ready
cd ../

# Test SmartCP imports
python -c "
import sys
sys.path.insert(0, '.')
from bifrost_extensions.client import GatewayClient
from bifrost_client import BifrostClient
print('✅ Python services ready')
"

# Test FastAPI server
python -c "
from fastapi import FastAPI
app = FastAPI()
print('✅ FastAPI ready')
"
```

### 4.3 Build Docker Images

```bash
# Build SmartCP API image
docker build -t smartcp-api:local -f Dockerfile .

# Verify image
docker images | grep smartcp-api

# Build Bifrost HTTP API image (if separate Dockerfile exists)
# docker build -t bifrost-http-api:local -f bifrost_api/Dockerfile .
```

---

## Step 5: Start Services

### 5.1 Start Infrastructure Services

```bash
# Start databases first
docker-compose up -d postgres redis neo4j

# Wait for health checks
echo "Waiting for services to be healthy..."
sleep 30

# Verify all healthy
docker-compose ps | grep "Up (healthy)"
```

### 5.2 Start Application Services

**⚠️ PARTIAL:** Only Python services can start. Go backend missing.

```bash
# Start Python services
docker-compose up -d api

# ❌ Cannot start Go backend (not implemented)
# docker-compose up -d bifrost-backend
```

### 5.3 Verify Service Health

```bash
#!/bin/bash
# Health check script

echo "Checking service health..."

# PostgreSQL
echo -n "PostgreSQL: "
if docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Redis
echo -n "Redis: "
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Neo4j
echo -n "Neo4j: "
if curl -s -u neo4j:password http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# SmartCP API
echo -n "SmartCP API: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Bifrost Backend (Go)
echo -n "Bifrost Backend: "
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy (NOT IMPLEMENTED)"
fi
```

---

## Step 6: Verify End-to-End

### 6.1 Test SmartCP API

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "ok"}

# List tools endpoint
curl http://localhost:8000/api/v1/tools | jq

# Should return: list of tools (if any registered)
```

### 6.2 Test Bifrost SDK (Python)

```python
# test_bifrost_sdk.py
from bifrost_extensions.client import GatewayClient

async def test_routing():
    client = GatewayClient(base_url="http://localhost:8001")

    result = await client.route(
        query="List all files in the current directory",
        strategy="model",
        use_cache=False
    )

    print(f"Route: {result.route}")
    print(f"Tools: {result.tools}")
    print(f"Confidence: {result.confidence}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_routing())
```

```bash
python test_bifrost_sdk.py
```

### 6.3 Test GraphQL API

**⚠️ BLOCKED:** GraphQL API not implemented.

```bash
# ❌ Cannot test (not implemented)
# curl -X POST http://localhost:8080/query \
#   -H "Content-Type: application/json" \
#   -d '{"query": "{ health { status } }"}'
```

### 6.4 Test Full Workflow

**⚠️ BLOCKED:** Cannot test full workflow without Go backend.

```bash
# Planned E2E test (after implementation):
# 1. Route query via GraphQL
# 2. Get tool list
# 3. Execute tool
# 4. Verify result
```

---

## Step 7: Access UIs

### 7.1 GraphQL Playground

**⚠️ NOT AVAILABLE:** Go backend not implemented.

```bash
# ❌ Not available yet
# open http://localhost:8080/
```

### 7.2 Swagger UI (SmartCP API)

```bash
# Open Swagger UI
open http://localhost:8000/docs

# Available endpoints:
# - GET /health
# - GET /api/v1/tools
# - POST /api/v1/route
# - POST /api/v1/execute
```

### 7.3 Prometheus Metrics

```bash
# SmartCP API metrics
curl http://localhost:8000/metrics

# Bifrost metrics (when implemented)
# curl http://localhost:8080/metrics
```

### 7.4 Database Clients

```bash
# PostgreSQL
psql -h localhost -U postgres -d smartcp

# Neo4j Browser
open http://localhost:7474
# Username: neo4j
# Password: password

# Redis CLI
docker-compose exec redis redis-cli
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Services Won't Start

**Symptoms:**
```bash
docker-compose up -d
# Some services fail to start
```

**Diagnosis:**
```bash
# Check service logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs neo4j
docker-compose logs api

# Check service status
docker-compose ps
```

**Solutions:**
- **Port conflicts:** Check if ports are already in use
  ```bash
  lsof -i :5432  # PostgreSQL
  lsof -i :6379  # Redis
  lsof -i :7474  # Neo4j HTTP
  lsof -i :7687  # Neo4j Bolt
  lsof -i :8000  # SmartCP API
  lsof -i :8080  # Bifrost Backend
  ```

- **Permission errors:** Ensure Docker has access to directories
  ```bash
  chmod -R 755 .
  ```

- **Resource limits:** Increase Docker memory/CPU
  ```bash
  # Docker Desktop → Settings → Resources
  # Set Memory: 8GB+
  # Set CPUs: 4+
  ```

#### Issue 2: Database Connection Errors

**Symptoms:**
```
Error: connection to server at "localhost", port 5432 failed
```

**Solutions:**
- Verify PostgreSQL is running:
  ```bash
  docker-compose ps postgres
  ```

- Check PostgreSQL logs:
  ```bash
  docker-compose logs postgres
  ```

- Test connection:
  ```bash
  docker-compose exec postgres pg_isready -U postgres
  ```

- Verify environment variables:
  ```bash
  echo $DATABASE_URL
  ```

#### Issue 3: Go Backend Missing

**Symptoms:**
```
Error: cannot find package "github.com/smartcp/bifrost/internal/graph"
```

**This is EXPECTED.** Go backend is not implemented yet.

**Workaround:**
- Use Python APIs only for now
- Skip GraphQL endpoints
- See `GAPS_ANALYSIS.md` for implementation plan

#### Issue 4: Health Checks Failing

**Symptoms:**
```bash
curl http://localhost:8000/health
# Connection refused
```

**Solutions:**
- Check if service is running:
  ```bash
  docker-compose ps api
  ```

- Check service logs:
  ```bash
  docker-compose logs -f api
  ```

- Verify environment variables:
  ```bash
  docker-compose exec api env | grep DATABASE
  ```

- Restart service:
  ```bash
  docker-compose restart api
  ```

#### Issue 5: Import Errors

**Symptoms:**
```python
ImportError: No module named 'bifrost_extensions'
```

**Solutions:**
- Activate virtual environment:
  ```bash
  source .venv/bin/activate
  ```

- Reinstall dependencies:
  ```bash
  pip install -r requirements.txt
  ```

- Verify Python path:
  ```python
  import sys
  print(sys.path)
  ```

---

## Cleanup

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DATA LOSS)
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### Remove Data

```bash
# Remove volumes
docker volume rm smartcp_postgres_data
docker volume rm smartcp_redis_data
docker volume rm smartcp_neo4j_data
docker volume rm smartcp_neo4j_logs

# Clean up logs
rm -rf logs/
```

### Reset Environment

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf .venv

# Remove environment file
rm .env.local

# Clean Docker
docker system prune -a
```

---

## Next Steps

### For Development

1. **Implement Go Backend** (See `GAPS_ANALYSIS.md` Gap 1)
   - Implement GraphQL schema
   - Implement resolvers
   - Implement services
   - Add tests

2. **Create Database Migrations** (See `GAPS_ANALYSIS.md` Gap 2)
   - Design schema
   - Create migration files
   - Test migrations

3. **Validate Orchestration** (See `GAPS_ANALYSIS.md` Gap 3)
   - Test service startup
   - Validate health checks
   - Verify networking

4. **Create E2E Tests** (See `GAPS_ANALYSIS.md` Gap 4)
   - Full workflow tests
   - Cross-service tests
   - Error handling tests

### For Production

See `PRODUCTION_DEPLOY_CHECKLIST.md` (to be created after local deployment works).

---

## Support

### Resources

- **Documentation:** `docs/`
- **API Reference:** http://localhost:8000/docs
- **GraphQL Schema:** `bifrost_backend/internal/graph/schema.graphqls` (when implemented)
- **Issues:** `GAPS_ANALYSIS.md`

### Getting Help

1. Check `GAPS_ANALYSIS.md` for known issues
2. Check `docs/troubleshooting/` for common problems
3. Check Docker logs: `docker-compose logs -f`
4. Check application logs: `logs/`

---

## Conclusion

**Current Status:** Local deployment is **NOT FUNCTIONAL** due to missing Go backend implementation.

**Required Work:** See `GAPS_ANALYSIS.md` for comprehensive gap analysis and implementation plan.

**Timeline:** 2-3 weeks to working local deployment (P0 gaps only).

**Recommendation:** Implement Go backend first. All other work is blocked.

---

**Last Updated:** December 2, 2025
**Status:** IMPLEMENTATION REQUIRED
**Version:** 1.0.0 (Planned)
