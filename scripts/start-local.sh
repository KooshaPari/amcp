#!/bin/bash
# Start all services locally via Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SmartCP Local Deployment Startup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}[1/5] Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    echo "Please start Docker Desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are available${NC}"

# Load environment variables
echo -e "\n${YELLOW}[2/5] Loading environment variables...${NC}"

if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Environment variables loaded from .env.local${NC}"
else
    echo -e "${YELLOW}⚠ .env.local not found, using defaults${NC}"
fi

# Check for API keys
echo -e "\n${YELLOW}[3/5] Checking API keys...${NC}"
missing_keys=0

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠ OPENAI_API_KEY not set${NC}"
    missing_keys=$((missing_keys + 1))
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠ ANTHROPIC_API_KEY not set${NC}"
    missing_keys=$((missing_keys + 1))
fi

if [ -z "$VOYAGE_API_KEY" ]; then
    echo -e "${YELLOW}⚠ VOYAGE_API_KEY not set${NC}"
    missing_keys=$((missing_keys + 1))
fi

if [ $missing_keys -gt 0 ]; then
    echo -e "${YELLOW}Note: $missing_keys API key(s) not set. Some features may not work.${NC}"
    echo -e "${YELLOW}Add your API keys to .env.local to enable all features.${NC}"
fi

# Build and start services
echo -e "\n${YELLOW}[4/5] Building and starting services...${NC}"
echo "This may take a few minutes on first run..."

docker-compose -f docker-compose.local.yml up -d --build

# Wait for services to be healthy
echo -e "\n${YELLOW}[5/5] Waiting for services to be healthy...${NC}"

max_wait=120
waited=0
interval=5

while [ $waited -lt $max_wait ]; do
    healthy_count=0
    total_count=0

    # Check each service
    for service in postgres redis qdrant smartcp bifrost-api bifrost-backend; do
        total_count=$((total_count + 1))
        if docker-compose -f docker-compose.local.yml ps | grep $service | grep -q "healthy\|running"; then
            healthy_count=$((healthy_count + 1))
        fi
    done

    if [ $healthy_count -eq $total_count ]; then
        echo -e "${GREEN}✓ All services are healthy!${NC}"
        break
    fi

    echo "Services ready: $healthy_count/$total_count (waited ${waited}s)"
    sleep $interval
    waited=$((waited + interval))
done

if [ $waited -ge $max_wait ]; then
    echo -e "${YELLOW}⚠ Timeout waiting for services. Some may still be starting...${NC}"
    echo "Run './scripts/health-check.sh' to check service status"
fi

# Display service URLs
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Service URLs:${NC}"
echo "  SmartCP MCP Server:    http://localhost:8000"
echo "  Bifrost HTTP API:      http://localhost:8001"
echo "  Bifrost GraphQL:       http://localhost:8080/graphql"
echo "  Bifrost ML Service:    http://localhost:8002"
echo ""
echo -e "${GREEN}Database & Infrastructure:${NC}"
echo "  PostgreSQL:            localhost:5432"
echo "  Redis:                 localhost:6379"
echo "  Qdrant (HTTP):         http://localhost:6333"
echo "  Qdrant (gRPC):         localhost:6334"
echo ""
echo -e "${GREEN}Useful Commands:${NC}"
echo "  View logs:             ./scripts/logs.sh [service]"
echo "  Check health:          ./scripts/health-check.sh"
echo "  Stop all services:     ./scripts/stop-local.sh"
echo ""
echo -e "${YELLOW}Run './scripts/health-check.sh' to verify all services${NC}"
