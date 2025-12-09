# DevOps Quick Start Guide

Quick reference for CI/CD operations in the SmartCP API project.

## 🚀 Quick Commands

### Local Development

```bash
# Install dependencies
make install

# Run all CI checks locally
make ci

# Start development environment
make dev

# Run tests
make test

# Format code
make format

# Run security checks
make security
```

### Docker Operations

```bash
# Build Docker image
make docker-build

# Run container
make docker-run

# Start all services (PostgreSQL, Redis, Neo4j)
make docker-up

# Stop all services
make docker-down

# View logs
make docker-logs
```

### Deployment

```bash
# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-production

# Or use script directly
./scripts/deploy.sh staging
./scripts/deploy.sh production
```

## 📋 CI/CD Workflows

### On Pull Request
- ✅ Linting (Ruff, Black)
- ✅ Type checking (MyPy)
- ✅ Unit tests
- ✅ Security scanning

### On Push to Main
- ✅ All PR checks
- ✅ Integration tests
- ✅ Docker build
- ✅ Staging deployment

### On Tag (v*)
- ✅ Full test suite
- ✅ Production deployment
- ✅ Docker image push to GHCR

### Nightly (2 AM UTC)
- ✅ Full test suite with all services
- ✅ Performance benchmarks
- ✅ Dependency audit

## 🔧 Setup

### 1. Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### 2. Configure GitHub Secrets

Required secrets for deployment:
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

Optional:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### 3. Environment Variables

Create `.env` file for local development:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/smartcp
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## 📊 Monitoring

- **CI Status**: GitHub Actions tab
- **Coverage**: Codecov dashboard
- **Security**: GitHub Security tab
- **Deployments**: Vercel dashboard

## 🐛 Troubleshooting

### Tests failing locally
```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
make clean
make install

# Run with verbose output
pytest tests/ -vv
```

### Docker issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

### Pre-commit hooks failing
```bash
# Update hooks
pre-commit autoupdate

# Run manually to see errors
pre-commit run --all-files
```

## 📚 More Information

- Full setup guide: [docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md)
- Workflow files: `.github/workflows/`
- Docker config: `Dockerfile`, `docker-compose.yml`
