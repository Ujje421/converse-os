FROM python:3.13-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

WORKDIR /app

# Copy shared kernel and auth service files
COPY packages/shared-kernel /app/packages/shared-kernel
COPY services/auth-service /app/services/auth-service

# Create virtual environment and install dependencies
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/services/auth-service
RUN uv pip install -e ../../packages/shared-kernel
RUN uv pip install -e .

# --- Runtime Stage ---
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies (e.g., for psycopg2/asyncpg if needed)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY services/auth-service/src /app/src
COPY services/auth-service/alembic /app/alembic
COPY services/auth-service/alembic.ini /app/

EXPOSE 8001

CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
