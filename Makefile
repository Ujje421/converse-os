# Converse AI Platform
# Multi-tenant SaaS platform for Conversational AI

.PHONY: setup up down restart logs build migrate test lint clean

# Environment variables
include .env.example
-include .env

export

# --- Setup & Infrastructure ---

setup:
	@echo "Setting up development environment..."
	@bash scripts/setup-dev.sh

up:
	@echo "Starting all services..."
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:
	@echo "Stopping all services..."
	docker compose down

restart: down up

logs:
	docker compose logs -f

build:
	docker compose build

# --- Database & Migrations ---

migrate:
	@echo "Running all database migrations..."
	@python scripts/migrate.py

seed:
	@echo "Seeding database with initial data..."
	@python scripts/seed.py

# --- Quality Assurance ---

test: test-unit test-integration

test-unit:
	@echo "Running unit tests across all packages..."
	uv run pytest tests/unit/

test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/integration/

lint:
	@echo "Running Ruff linter..."
	uv run ruff check .
	@echo "Running Mypy type checker..."
	uv run mypy .

format:
	@echo "Formatting code..."
	uv run ruff format .
	uv run ruff check --fix .

# --- Maintenance ---

clean:
	@echo "Cleaning up Python artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
