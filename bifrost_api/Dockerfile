# Dockerfile for Bifrost HTTP API (Python FastAPI)
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY ../requirements.txt /app/
COPY ../pyproject.toml* /app/

# Install dependencies
RUN uv pip install --system --no-cache -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser bifrost_api/ /app/bifrost_api/
COPY --chown=appuser:appuser bifrost/ /app/bifrost/
COPY --chown=appuser:appuser infrastructure/ /app/infrastructure/
COPY --chown=appuser:appuser models/ /app/models/
COPY --chown=appuser:appuser services/ /app/services/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "bifrost_api.app:app", "--host", "0.0.0.0", "--port", "8001"]
