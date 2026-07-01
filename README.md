# Converse Enterprise Conversational AI Platform

> A production-grade, multi-tenant SaaS platform that allows enterprises to create, deploy, manage, monitor, and optimize conversational AI agents powered by Dialogflow CX and Large Language Models.

## 🌟 Overview

Converse is a massive microservices architecture built with Domain Driven Design (DDD) principles. It handles end-to-end conversational AI lifecycles for multiple organizations in complete isolation.

## 🏗️ Architecture

- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0, Celery
- **Databases**: PostgreSQL (with pgvector), Redis
- **Messaging**: Apache Kafka
- **Observability**: OpenTelemetry, Prometheus, Grafana
- **AI Integrations**: Dialogflow CX, Vertex AI / Gemini, OpenAI, Anthropic

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.13+
- `uv` package manager

### Local Setup

1. **Clone the repository**
2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your specific API keys
   ```
3. **Start Infrastructure**
   ```bash
   make up
   ```
4. **Run Migrations & Seed Data**
   ```bash
   make migrate
   make seed
   ```

## 📚 Documentation

See the `/docs` folder for detailed architectural decisions, API contracts, and guides.
