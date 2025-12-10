# Docker Configuration

## Overview

SmartCP includes Docker configurations for local development and testing.

## Files

### `docker-compose.yml`
**Purpose**: Local development environment for SmartCP API

**Services**:
- `api` - SmartCP FastAPI application
- `postgres` - PostgreSQL database (v16)
- `redis` - Redis cache (v7)
- `neo4j` - Neo4j graph database (v5)

**Usage**:
```bash
docker-compose up -d
```

### `docker-compose.local.example.yml`
**Purpose**: Example configuration for E2E testing with full Bifrost stack

**Services**:
- `bifrost` - Bifrost Gateway
- `graphql` - Go GraphQL backend
- `grpc` - MLX gRPC service
- `db` - PostgreSQL for testing
- `smartcp` - SmartCP HTTP endpoint
- `redis` - Redis cache

**Usage**:
```bash
cp docker-compose.local.example.yml docker-compose.local.yml
# Edit docker-compose.local.yml with your settings
docker-compose -f docker-compose.local.yml up -d
```

## Notes

- These configs are for local development/testing only
- Production deployments use different configurations
- Go code (`smartcpcli`) is built separately, not via Docker
