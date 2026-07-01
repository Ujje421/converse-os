#!/bin/bash
set -e

# Initializes all databases for the different microservices
# Mounted into the postgres container

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    -- Enable pgvector extension on the main db
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Create individual databases
    CREATE DATABASE converse_auth;
    CREATE DATABASE converse_users;
    CREATE DATABASE converse_orgs;
    CREATE DATABASE converse_agents;
    CREATE DATABASE converse_conversations;
    CREATE DATABASE converse_workflows;
    CREATE DATABASE converse_webhooks;
    CREATE DATABASE converse_knowledge;
    CREATE DATABASE converse_llm;
    CREATE DATABASE converse_prompts;
    CREATE DATABASE converse_analytics;
    CREATE DATABASE converse_notifications;
    CREATE DATABASE converse_audit;
    CREATE DATABASE converse_billing;
    CREATE DATABASE converse_admin;
    CREATE DATABASE converse_search;
EOSQL
