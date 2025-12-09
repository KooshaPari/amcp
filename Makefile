.PHONY: help install test lint format type-check security clean build-wheels build-constraints build-go build-go-all build-cli build-cli-all deploy

help: ## Show this help message
	@echo "SmartCP API - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt || true
	pre-commit install

test: ## Run tests
	pytest tests/ -v --cov=. --cov-report=term --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/ -m "unit or not (integration or e2e)" -v

test-integration: ## Run integration tests
	pytest tests/ -m integration -v

test-coverage: ## Run tests with coverage report
	pytest tests/ --cov=. --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

lint: ## Run linters
	ruff check .
	black --check .

format: ## Format code
	ruff format .
	black .

type-check: ## Run type checker
	mypy . --ignore-missing-imports

security: ## Run security checks
	safety check
	bandit -r . -f json -o bandit-report.json || true

clean: ## Clean temporary files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml *.log dist/ wheelhouse/ bin/

# ---------- Native build artifacts (no Docker) ----------

build-wheels: ## Build Python wheels into wheelhouse/ (smartcp + deps)
	python -m build --wheel --outdir wheelhouse .

build-constraints: ## Export pinned constraints from pyproject
	pip install uv >/dev/null 2>&1 || true
	uv pip compile pyproject.toml --all-extras -o constraints.txt

build-go: ## Build bifrost-backend for host OS/arch
	cd bifrost_backend && go build -o ../bin/bifrost-backend ./cmd/server

build-go-all: ## Cross-build bifrost-backend (linux/windows/darwin; amd64+arm64)
	mkdir -p bin
	cd bifrost_backend && GOOS=linux   GOARCH=amd64 go build -o ../bin/bifrost-backend-linux-amd64   ./cmd/server
	cd bifrost_backend && GOOS=linux   GOARCH=arm64 go build -o ../bin/bifrost-backend-linux-arm64   ./cmd/server
	cd bifrost_backend && GOOS=darwin  GOARCH=arm64 go build -o ../bin/bifrost-backend-darwin-arm64  ./cmd/server
	cd bifrost_backend && GOOS=darwin  GOARCH=amd64 go build -o ../bin/bifrost-backend-darwin-amd64 ./cmd/server
	cd bifrost_backend && GOOS=windows GOARCH=amd64 go build -o ../bin/bifrost-backend-windows-amd64.exe ./cmd/server

build-cli: ## Build smartcpcli (Go) for host
\tgo build -o bin/smartcpcli ./cmd/smartcpcli

build-cli-all: ## Cross-build smartcpcli (linux/darwin/windows; amd64+arm64)
\tmkdir -p bin
\tGOOS=linux   GOARCH=amd64 go build -o bin/smartcpcli-linux-amd64   ./cmd/smartcpcli
\tGOOS=linux   GOARCH=arm64 go build -o bin/smartcpcli-linux-arm64   ./cmd/smartcpcli
\tGOOS=darwin  GOARCH=arm64 go build -o bin/smartcpcli-darwin-arm64  ./cmd/smartcpcli
\tGOOS=windows GOARCH=amd64 go build -o bin/smartcpcli-windows-amd64.exe ./cmd/smartcpcli

deploy-staging: ## Deploy to staging
	./scripts/deploy.sh staging

deploy-production: ## Deploy to production
	./scripts/deploy.sh production

ci: lint type-check test ## Run all CI checks locally

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files
