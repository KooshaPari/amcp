#!/bin/bash
# View logs for SmartCP services

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVICE=${1:-}
FOLLOW=${2:--f}

if [ -z "$SERVICE" ]; then
    echo -e "${YELLOW}Usage: ./scripts/logs.sh [service] [options]${NC}"
    echo ""
    echo "Services:"
    echo "  smartcp           - SmartCP FastMCP server"
    echo "  bifrost-api       - Bifrost HTTP API"
    echo "  bifrost-backend   - Bifrost GraphQL backend"
    echo "  bifrost-ml        - Bifrost ML service"
    echo "  postgres          - PostgreSQL database"
    echo "  redis             - Redis cache"
    echo "  qdrant            - Qdrant vector database"
    echo "  all               - All services"
    echo ""
    echo "Options:"
    echo "  -f                - Follow logs (default)"
    echo "  --tail=N          - Show last N lines"
    echo ""
    echo "Examples:"
    echo "  ./scripts/logs.sh smartcp"
    echo "  ./scripts/logs.sh bifrost-api --tail=100"
    echo "  ./scripts/logs.sh all"
    exit 0
fi

if [ "$SERVICE" = "all" ]; then
    echo -e "${GREEN}Following logs for all services...${NC}"
    docker-compose -f docker-compose.local.yml logs $FOLLOW
else
    echo -e "${GREEN}Following logs for $SERVICE...${NC}"
    docker-compose -f docker-compose.local.yml logs $FOLLOW $SERVICE
fi
