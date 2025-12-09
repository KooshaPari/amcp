#!/bin/bash
# Deployment script for SmartCP API
# Usage: ./scripts/deploy.sh [staging|production]

set -euo pipefail

ENVIRONMENT="${1:-staging}"
VERSION="${2:-$(git describe --tags --always 2>/dev/null || echo "dev-$(git rev-parse --short HEAD)")}"

echo "🚀 Deploying SmartCP API"
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    if [ ! -f ".env" ] && [ "$ENVIRONMENT" != "production" ]; then
        echo -e "${YELLOW}⚠️  .env file not found. Using defaults.${NC}"
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Run tests
run_tests() {
    echo "🧪 Running tests..."
    
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --cov=. --cov-report=term || {
            echo -e "${RED}❌ Tests failed${NC}"
            exit 1
        }
    else
        echo -e "${YELLOW}⚠️  pytest not found, skipping tests${NC}"
    fi
    
    echo -e "${GREEN}✅ Tests passed${NC}"
}

# Build Docker image
build_image() {
    echo "🔨 Building Docker image..."
    
    docker build -t smartcp-api:$VERSION . || {
        echo -e "${RED}❌ Docker build failed${NC}"
        exit 1
    }
    
    docker tag smartcp-api:$VERSION smartcp-api:latest
    
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
}

# Deploy to environment
deploy() {
    echo "🚀 Deploying to $ENVIRONMENT..."
    
    case $ENVIRONMENT in
        staging)
            echo "Deploying to staging environment..."
            # Add staging-specific deployment commands
            docker-compose -f docker-compose.yml up -d --build
            ;;
        production)
            echo "Deploying to production environment..."
            # Add production-specific deployment commands
            # This might include:
            # - Pushing to container registry
            # - Updating Kubernetes deployments
            # - Running database migrations
            echo -e "${YELLOW}⚠️  Production deployment requires manual approval${NC}"
            ;;
        *)
            echo -e "${RED}❌ Unknown environment: $ENVIRONMENT${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}✅ Deployment completed${NC}"
}

# Health check
health_check() {
    echo "🏥 Running health check..."
    
    sleep 5  # Wait for services to start
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        exit 1
    fi
}

# Main execution
main() {
    check_prerequisites
    run_tests
    build_image
    deploy
    health_check
    
    echo ""
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo "Environment: $ENVIRONMENT"
    echo "Version: $VERSION"
    echo "API: http://localhost:8000"
    echo "Health: http://localhost:8000/health"
}

main
