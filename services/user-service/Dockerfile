FROM python:3.13-slim as builder

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

WORKDIR /app

COPY packages/shared-kernel /app/packages/shared-kernel
COPY services/user-service /app/services/user-service

RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/services/user-service
RUN uv pip install -e ../../packages/shared-kernel
RUN uv pip install -e .

FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY services/user-service/src /app/src
COPY services/user-service/alembic /app/alembic
COPY services/user-service/alembic.ini /app/

EXPOSE 8002

CMD ["uvicorn", "user_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
