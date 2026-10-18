# ==============================================================================
# ClassLens FastAPI Backend Production Dockerfile (Multi-Stage Build)
# ==============================================================================

# Stage 1: Build dependencies with compiler toolchain
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Minimal production runtime
FROM python:3.12-slim AS runner

WORKDIR /app

# Non-root user security enforcement
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Copy application code & verified synthetic fixtures
COPY services/ ./services/
COPY scripts/ ./scripts/
COPY tests/fixtures/ ./tests/fixtures/
COPY dataset/ ./dataset/
COPY pyproject.toml README.md ./

# Create runtime directories for isolated local storage fallback if needed
RUN mkdir -p /app/local-data/store /app/local-data/uploads && \
    chown -R appuser:appgroup /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
