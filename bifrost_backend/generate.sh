#!/bin/bash
set -e

echo "Installing dependencies..."
go mod download
go get github.com/99designs/gqlgen@latest

echo "Generating GraphQL code..."
go run github.com/99designs/gqlgen generate

echo "Generation complete!"
echo "To build: go build -o bifrost cmd/server/main.go"
echo "To run: ./bifrost or go run cmd/server/main.go"
