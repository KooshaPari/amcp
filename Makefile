.PHONY: help install test lint format type-check security clean docker-build docker-run docker-up docker-down deploy

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
	rm -rf htmlcov/ .coverage coverage.xml *.log

docker-build: ## Build Docker image
	docker build -t smartcp-api:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env smartcp-api:latest

docker-up: ## Start services with docker-compose
	docker-compose up -d

docker-down: ## Stop services with docker-compose
	docker-compose down

docker-logs: ## View docker-compose logs
	docker-compose logs -f api

deploy-staging: ## Deploy to staging
	./scripts/deploy.sh staging

deploy-production: ## Deploy to production
	./scripts/deploy.sh production

ci: lint type-check test ## Run all CI checks locally

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

dev: ## Start development environment
	docker-compose up -d
	@echo "Services started. API available at http://localhost:8000"

stop: ## Stop all services
	docker-compose down
	@echo "All services stopped"
