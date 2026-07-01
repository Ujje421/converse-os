"""Converse AI - Organization Service"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI

from converse_shared.fastapi import create_app
from converse_shared.infrastructure.health import HealthCheckRegistry
from converse_shared.infrastructure.database import DatabaseManager
from converse_shared.infrastructure.cache import CacheManager
from converse_shared.infrastructure.messaging import KafkaProducerManager
from converse_shared.infrastructure.event_bus import KafkaEventBus, InProcessEventBus
from converse_shared.application.mediator import Mediator
from converse_shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

from org_service.config.settings import settings
from org_service.infrastructure.persistence.org_repo_impl import SqlOrganizationRepository
from org_service.application.commands.create_org import CreateOrgCommand, CreateOrgCommandHandler
from org_service.api.v1.org_controller import router as org_router

logger = structlog.get_logger()

# --- Infrastructure Setup ---

db_manager = DatabaseManager(
    database_url=settings.database_url,
    echo=settings.debug,
)

cache_manager = CacheManager(
    redis_url=settings.redis_url,
    key_prefix="converse:org",
)

kafka_producer = KafkaProducerManager(
    bootstrap_servers=settings.kafka_bootstrap_servers,
    client_id="org-service-producer",
)

in_process_bus = InProcessEventBus()
event_bus = KafkaEventBus(
    producer=kafka_producer,
    topic_prefix="converse.orgs",
    in_process_bus=in_process_bus,
)

mediator = Mediator()

# --- Health Checks ---

health_registry = HealthCheckRegistry(
    service_name=settings.service_name,
    version=settings.service_version,
)

async def check_db():
    async with db_manager.engine.connect() as conn:
        from sqlalchemy import text
        await conn.execute(text("SELECT 1"))
    return True

health_registry.register("postgres", check_db)
health_registry.register("redis", cache_manager.health_check)
health_registry.register("kafka_producer", kafka_producer.health_check)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("org_service_initializing")
    await db_manager.initialize()
    await cache_manager.initialize()
    await kafka_producer.initialize()
    
    yield
    
    logger.info("org_service_shutting_down")
    await kafka_producer.close()
    await cache_manager.close()
    await db_manager.close()


# --- Application Factory ---

app = create_app(
    settings=settings,
    health_registry=health_registry,
    lifespan=lifespan,
)

# --- Dependency Injection / CQRS Registration ---

def get_uow() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(db_manager.session_factory, event_bus)

def get_repo(uow: SqlAlchemyUnitOfWork | None = None) -> SqlOrganizationRepository:
    session = uow.session if uow else db_manager.session_factory()
    return SqlOrganizationRepository(session)

# Register Handlers
mediator.register(
    CreateOrgCommand,
    lambda: CreateOrgCommandHandler(
        uow=(uow := get_uow()),
        repo=get_repo(uow)
    )
)


# --- API Routes ---

app.include_router(org_router)
