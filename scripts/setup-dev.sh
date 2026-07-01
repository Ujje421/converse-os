#!/bin/bash
set -e

echo "================================================="
echo " Converse AI Platform - Dev Environment Setup    "
echo "================================================="

# Ensure UV is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install it first: https://docs.astral.sh/uv/"
    exit 1
fi

echo "1. Generating JWT keys..."
bash scripts/generate-keys.sh

echo "2. Installing dependencies across all services..."
make install

echo "3. Starting infrastructure containers (Postgres, Redis, Kafka, etc.)..."
docker-compose -f docker-compose.yml up -d

echo "4. Waiting for databases to be ready..."
sleep 5 # Simple wait, could be enhanced with pg_isready loops

echo "5. Initializing databases (Roles & schemas)..."
bash scripts/init-dbs.sh

echo "6. Running Alembic migrations for all services..."
make migrate

echo "7. Seeding default data..."
uv run scripts/seed.py

echo ""
echo "================================================="
echo " Setup Complete! "
echo " You can now start the services using:"
echo "   make dev"
echo "================================================="
