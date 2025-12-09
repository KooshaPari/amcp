#!/bin/bash
# Stop all local services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping all SmartCP services...${NC}"

# Stop services
docker-compose -f docker-compose.local.yml down

echo -e "${GREEN}✓ All services stopped${NC}"
echo ""
echo "To also remove volumes (database data), run:"
echo "  docker-compose -f docker-compose.local.yml down -v"
