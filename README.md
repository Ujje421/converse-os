# Converse AI Platform

An Enterprise-grade Conversational AI Platform enabling multi-tenant agent management, utilizing Dialogflow CX and leading LLMs (OpenAI, Vertex AI, Anthropic). Built with modern Python and Hexagonal/Clean Architecture.

## Architecture

Converse AI is a microservices platform connected via HTTP APIs and asynchronous Kafka event streams. It employs CQRS patterns, Unit of Work, and Domain-Driven Design (DDD).

### Core Components

1. **API Gateway**: Reverse proxy handling routing, rate limiting, and centralized auth validation.
2. **Auth Service**: Manages users, credentials, and issues JWTs (RS256).
3. **User Service**: Manages user profiles and preferences.
4. **Organization Service**: Multi-tenant core, managing orgs, billing plans, and RBAC memberships.
5. **Agent Service**: Defines conversational agents, LLM settings, and prompts.
6. **Audit Service**: Immutable compliance logging via event streams/APIs.
7. **Shared Kernel**: Common infrastructure containing `SqlAlchemyUnitOfWork`, `Mediator` (CQRS), `KafkaEventBus`, Telemetry, and Base Entities.

### Tech Stack

- **Language**: Python 3.13
- **Framework**: FastAPI
- **Data Access**: SQLAlchemy 2.0 (asyncpg) + Alembic
- **Databases**: PostgreSQL (Service-per-DB), Redis (Caching & Rate Limiting)
- **Messaging**: Apache Kafka
- **Observability**: OpenTelemetry, Prometheus, Jaeger

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.13
- [uv](https://docs.astral.sh/uv/) (Fast Python package manager)
- OpenSSL (for JWT key generation)

### Setup

Run the comprehensive setup script:
```bash
bash scripts/setup-dev.sh
```

This will:
1. Generate RSA keys for JWT.
2. Install all dependencies using `uv`.
3. Start infrastructure (Postgres, Redis, Kafka, Prometheus).
4. Run database initialization and Alembic migrations.
5. Seed the database with a default Admin user and Organization.

### Running the Services

Start all API microservices simultaneously via Honcho (managed by Makefile):
```bash
make dev
```
Services will be accessible at:
- API Gateway: `http://localhost:8000`
- Auth Service: `http://localhost:8001`
- User Service: `http://localhost:8002`
- Org Service: `http://localhost:8003`
- Agent Service: `http://localhost:8004`
- Audit Service: `http://localhost:8005`

### Running Tests

```bash
make test
```
