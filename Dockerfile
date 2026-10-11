# ==============================================================================
# Meross Dual Gateway - Production Container
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Build wheel package
RUN pip install --no-cache-dir build && python -m build --wheel

# ------------------------------------------------------------------------------
# Final Runtime Stage
# ------------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Create unprivileged user (UID 1000)
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Install built wheel
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl curl && rm -rf /tmp/*.whl

USER appuser

EXPOSE 8112

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8112/healthz')" || exit 1

ENTRYPOINT ["meross-mcp"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8112"]
