#!/bin/bash
set -e

echo "🚀 Bifrost GraphQL Server - Quick Start"
echo "========================================"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    echo ""
    echo "Please set it first:"
    echo "  export DATABASE_URL='postgres://user:password@localhost:5432/bifrost?sslmode=disable'"
    exit 1
fi

echo "✅ DATABASE_URL configured"

# Check if database exists
if ! psql "$DATABASE_URL" -c '\q' 2>/dev/null; then
    echo "📦 Database not found, creating..."
    DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^?]+).*|\1|')
    psql postgres -c "CREATE DATABASE $DB_NAME" 2>/dev/null || echo "Database may already exist"
fi

# Initialize schema
echo "📊 Initializing database schema..."
psql "$DATABASE_URL" -f schema.sql > /dev/null 2>&1 || echo "Schema may already exist"

# Build if binary doesn't exist
if [ ! -f "./bifrost" ]; then
    echo "🔨 Building server..."
    go build -o bifrost cmd/server/main.go
fi

echo "✅ Server ready!"
echo ""
echo "Starting Bifrost GraphQL Server..."
echo "  GraphQL Playground: http://localhost:8080"
echo "  GraphQL Endpoint: http://localhost:8080/query"
echo "  Health Check: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run server
./bifrost
