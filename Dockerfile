# Multi-stage Dockerfile for Ebook-MCP server
# Stage 1: Build virtual environment using uv
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation and copy mode for uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency definition files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies (excluding dev dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Stage 2: Minimal runtime image
FROM python:3.12-slim-bookworm AS runner

# Create non-root user and group (UID/GID 10001)
RUN groupadd -g 10001 ebookmcp && \
    useradd -u 10001 -g ebookmcp -s /bin/false -m ebookmcp

WORKDIR /app

# Copy virtual environment and source code from builder stage
COPY --from=builder --chown=ebookmcp:ebookmcp /app /app

# Environment configuration
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EBOOK_MCP_TRANSPORT=sse \
    EBOOK_MCP_HOST=0.0.0.0 \
    EBOOK_MCP_PORT=8000 \
    EBOOK_MCP_LOG_DIR=/home/ebookmcp/.local/state/ebook-mcp/logs \
    EBOOK_MCP_ALLOWED_DIR=/library

# Create default directories with correct non-root permissions
RUN mkdir -p /library /home/ebookmcp/.local/state/ebook-mcp/logs && \
    chown -R ebookmcp:ebookmcp /library /home/ebookmcp

USER ebookmcp:ebookmcp

EXPOSE 8000

# Health check for SSE transport mode
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/sse')" || exit 1

ENTRYPOINT ["ebook-mcp"]
