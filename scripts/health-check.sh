#!/bin/bash
# Check health of all SmartCP services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SmartCP Service Health Check${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

check_http_service() {
    local name=$1
    local url=$2
    local timeout=${3:-5}

    echo -n "Checking $name... "
    if curl -sf --max-time $timeout "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        return 1
    fi
}

check_tcp_service() {
    local name=$1
    local host=$2
    local port=$3

    echo -n "Checking $name... "
    if nc -z -w 5 $host $port 2>/dev/null; then
        echo -e "${GREEN}✓ Reachable${NC}"
        return 0
    else
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    fi
}

all_healthy=0

# Check HTTP services
echo -e "${YELLOW}HTTP Services:${NC}"
check_http_service "SmartCP MCP Server" "http://localhost:8000/health" || all_healthy=1
check_http_service "Bifrost HTTP API" "http://localhost:8001/health" || all_healthy=1
check_http_service "Bifrost GraphQL" "http://localhost:8080/health" || all_healthy=1
check_http_service "Bifrost ML Service" "http://localhost:8002/health" 10 || all_healthy=1
echo ""

# Check infrastructure services
echo -e "${YELLOW}Infrastructure Services:${NC}"
check_tcp_service "PostgreSQL" "localhost" 5432 || all_healthy=1
check_tcp_service "Redis" "localhost" 6379 || all_healthy=1
check_http_service "Qdrant" "http://localhost:6333/health" || all_healthy=1
echo ""

# Check Docker containers
echo -e "${YELLOW}Container Status:${NC}"
docker-compose -f docker-compose.local.yml ps
echo ""

# Final summary
if [ $all_healthy -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All services are healthy! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Some services are unhealthy${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: ./scripts/logs.sh [service]"
    echo "  2. Restart services: ./scripts/stop-local.sh && ./scripts/start-local.sh"
    echo "  3. Check Docker: docker ps"
    exit 1
fi
