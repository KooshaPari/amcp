.PHONY: help install generate build run test clean docker db-init db-reset

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	go mod download
	go get github.com/99designs/gqlgen@latest

generate: ## Generate GraphQL code
	go run github.com/99designs/gqlgen generate

build: generate ## Build binary
	go build -o bifrost cmd/server/main.go

run: ## Run server
	go run cmd/server/main.go

test: ## Run tests
	go test -v ./...

test-coverage: ## Run tests with coverage
	go test -v -cover -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

clean: ## Clean generated files and binaries
	rm -f bifrost
	rm -f coverage.out coverage.html
	rm -rf internal/graph/generated.go internal/graph/model/

docker-build: ## Build Docker image
	docker build -t bifrost:latest .

docker-run: ## Run Docker container
	docker run -p 8080:8080 \
		-e DATABASE_URL="$(DATABASE_URL)" \
		bifrost:latest

db-init: ## Initialize database
	psql $(DATABASE_URL) -f schema.sql

db-reset: ## Reset database (WARNING: deletes all data)
	psql $(DATABASE_URL) -c "DROP TABLE IF EXISTS tools CASCADE;"
	$(MAKE) db-init

dev: ## Run in development mode with auto-reload
	go run github.com/cosmtrek/air@latest

fmt: ## Format code
	go fmt ./...
	go vet ./...

lint: ## Run linters
	golangci-lint run

deps-update: ## Update dependencies
	go get -u ./...
	go mod tidy

.DEFAULT_GOAL := help
