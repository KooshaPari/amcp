# CI/CD Infrastructure Setup Guide

This document describes the CI/CD infrastructure for the SmartCP API project.

## Overview

The project uses GitHub Actions for continuous integration and deployment. The CI/CD pipeline includes:

- **Linting & Formatting**: Ruff and Black
- **Type Checking**: MyPy
- **Testing**: Pytest with coverage reporting
- **Security Scanning**: Safety, Bandit, and Trivy
- **Docker Builds**: Multi-arch container images
- **Deployment**: Vercel and Docker registry

## Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)

Runs on every PR and push to main/develop:

- **Lint**: Code quality checks with Ruff and Black
- **Type Check**: Static type analysis with MyPy
- **Unit Tests**: Fast unit tests with coverage
- **Integration Tests**: Full integration tests (main/develop only)
- **Security**: Vulnerability scanning

**Duration**: ~15-30 minutes

### 2. Deploy Pipeline (`.github/workflows/deploy.yml`)

Runs on:
- Push to `main` (staging deployment)
- Tags matching `v*` (production deployment)
- Manual workflow dispatch

**Steps**:
1. Prepare deployment configuration
2. Run full test suite (unless skipped)
3. Deploy to Vercel
4. Build and push Docker image to GHCR
5. Send deployment notifications

**Duration**: ~20-40 minutes

### 3. Nightly Tests (`.github/workflows/nightly.yml`)

Runs daily at 2 AM UTC:

- Full test suite with all services
- Performance benchmarks
- Dependency audit

**Duration**: ~60 minutes

## Setup Instructions

### 1. GitHub Secrets

Configure the following secrets in your GitHub repository:

```bash
# Vercel Deployment
VERCEL_TOKEN=your_vercel_token
VERCEL_ORG_ID=your_org_id
VERCEL_PROJECT_ID=your_project_id

# Optional: Additional deployment targets
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

**To get Vercel credentials**:
1. Go to Vercel Dashboard → Settings → Tokens
2. Create a new token
3. Get Org ID and Project ID from project settings

### 2. Pre-commit Hooks

Install pre-commit hooks for local development:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### 3. Local Testing

Test the CI pipeline locally:

```bash
# Run linting
ruff check .
ruff format --check .

# Run type checking
mypy . --ignore-missing-imports

# Run tests
pytest tests/ -v --cov=. --cov-report=term

# Run security checks
safety check
bandit -r . -f json
```

### 4. Docker Build

Build and test Docker image locally:

```bash
# Build image
docker build -t smartcp-api:latest .

# Run container
docker run -p 8000:8000 smartcp-api:latest

# Test with docker-compose
docker-compose up -d
docker-compose logs -f api
```

## Environment Configuration

### Development

```bash
# Local development
export DATABASE_URL="postgresql://user:pass@localhost:5432/smartcp"
export REDIS_URL="redis://localhost:6379"
export NEO4J_URI="bolt://localhost:7687"
```

### Staging/Production

Configure environment variables in:
- Vercel Dashboard (for Vercel deployments)
- GitHub Environments (for workflow deployments)
- Docker/Kubernetes secrets (for container deployments)

## Monitoring

### Code Coverage

Coverage reports are uploaded to Codecov automatically. View reports at:
- Codecov Dashboard: https://codecov.io/gh/your-org/smartcp

### Security Alerts

Security scan results are available in:
- GitHub Security Tab → Code scanning alerts
- Trivy SARIF reports

### Deployment Status

Monitor deployments in:
- GitHub Actions tab
- Vercel Dashboard
- Container Registry (GHCR)

## Troubleshooting

### Common Issues

1. **Tests failing in CI but passing locally**
   - Check Python version compatibility
   - Verify environment variables are set correctly
   - Check service dependencies (PostgreSQL, Redis, Neo4j)

2. **Docker build failing**
   - Verify Dockerfile syntax
   - Check for missing dependencies in requirements.txt
   - Ensure .dockerignore is configured correctly

3. **Deployment failing**
   - Verify Vercel credentials are correct
   - Check environment variables in Vercel dashboard
   - Review deployment logs in GitHub Actions

4. **Pre-commit hooks failing**
   - Run `pre-commit run --all-files` to see detailed errors
   - Update hooks: `pre-commit autoupdate`
   - Skip hooks temporarily: `git commit --no-verify` (not recommended)

### Getting Help

- Check workflow logs in GitHub Actions
- Review error messages in workflow runs
- Consult project documentation
- Open an issue with workflow logs attached

## Best Practices

1. **Always run pre-commit hooks before pushing**
2. **Keep dependencies up to date** (check nightly reports)
3. **Monitor security alerts** regularly
4. **Review deployment logs** after each deployment
5. **Test locally** before pushing to main

## Advanced Configuration

### Custom Test Matrices

Modify the Python version matrix in `ci.yml`:

```yaml
strategy:
  matrix:
    python-version: ['3.12', '3.13']
```

### Custom Deployment Targets

Add additional deployment jobs in `deploy.yml`:

```yaml
deploy-custom:
  name: Deploy to Custom Target
  runs-on: ubuntu-latest
  steps:
    - name: Custom deployment
      run: |
        # Your deployment commands
```

### Performance Thresholds

Set performance thresholds in `nightly.yml`:

```yaml
- name: Check performance
  run: |
    pytest tests/ -m performance --benchmark-json=benchmark.json
    python scripts/check_performance.py benchmark.json
```

## Maintenance

### Regular Tasks

- **Weekly**: Review security reports
- **Monthly**: Update dependencies
- **Quarterly**: Review and optimize CI/CD workflows
- **As needed**: Update deployment configurations

### Updating Workflows

1. Make changes to workflow files
2. Test locally when possible
3. Create a PR with workflow changes
4. Review in GitHub Actions preview
5. Merge and monitor first run
