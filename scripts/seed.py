#!/usr/bin/env python3
"""
Seed Data Script for Converse AI Platform

This script initializes the databases with default data for local development:
- Default Tenant / Organization
- Admin User
- Example Agent
"""

import asyncio
import uuid
import sys
import os

# Add services to sys.path to allow importing their ORM models
sys.path.append(os.path.join(os.path.dirname(__file__), "../packages/shared-kernel/src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../services/auth-service/src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../services/user-service/src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../services/org-service/src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../services/agent-service/src"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Import models
from auth_service.infrastructure.persistence.models import UserCredentialModel
from user_service.infrastructure.persistence.models import UserProfileModel
from org_service.infrastructure.persistence.models import OrganizationModel, OrganizationMemberModel
from agent_service.infrastructure.persistence.models import AgentModel
from converse_shared.security.password import PasswordHasher

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_USER = os.getenv("POSTGRES_USER", "converse")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "converse_secret_change_me")


async def create_engine_and_session(db_name: str):
    url = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{db_name}"
    engine = create_async_engine(url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


async def seed():
    print("Seeding Converse AI Platform...")

    admin_id = uuid.uuid4()
    org_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    
    admin_email = "admin@converse.ai"
    admin_password = "AdminPassword123!"

    print(f"Creating Admin User: {admin_email}")
    # 1. Auth Service
    auth_engine, auth_session = await create_engine_and_session("converse_auth")
    async with auth_session() as session:
        hasher = PasswordHasher()
        cred = UserCredentialModel(
            id=admin_id,
            email=admin_email,
            password_hash=hasher.hash(admin_password),
            is_active=True,
            is_verified=True,
            failed_login_attempts=0
        )
        session.add(cred)
        await session.commit()
    await auth_engine.dispose()

    # 2. User Service
    user_engine, user_session = await create_engine_and_session("converse_users")
    async with user_session() as session:
        profile = UserProfileModel(
            id=admin_id,
            email=admin_email,
            first_name="Converse",
            last_name="Admin",
            timezone="UTC",
            preferences={}
        )
        session.add(profile)
        await session.commit()
    await user_engine.dispose()
    
    print(f"Creating Default Organization: Acme Corp (ID: {org_id})")
    # 3. Org Service
    org_engine, org_session = await create_engine_and_session("converse_orgs")
    async with org_session() as session:
        org = OrganizationModel(
            id=org_id,
            name="Acme Corp",
            slug="acme-corp",
            billing_plan="ENTERPRISE",
            is_active=True,
            settings={}
        )
        member = OrganizationMemberModel(
            id=uuid.uuid4(),
            org_id=org_id,
            user_id=admin_id,
            role="OWNER"
        )
        session.add(org)
        session.add(member)
        await session.commit()
    await org_engine.dispose()
    
    print(f"Creating Default Agent: Support Bot (ID: {agent_id})")
    # 4. Agent Service
    agent_engine, agent_session = await create_engine_and_session("converse_agents")
    async with agent_session() as session:
        agent = AgentModel(
            id=agent_id,
            org_id=org_id,
            name="Support Bot",
            description="Default customer support agent for Acme Corp",
            llm_provider="openai",
            model_name="gpt-4",
            system_prompt="You are a helpful customer support assistant for Acme Corp.",
            settings={"temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_tokens": 2048},
            is_active=True
        )
        session.add(agent)
        await session.commit()
    await agent_engine.dispose()
    
    print("\n--- Seeding Complete ---")
    print(f"Admin Email: {admin_email}")
    print(f"Admin Password: {admin_password}")


if __name__ == "__main__":
    asyncio.run(seed())
