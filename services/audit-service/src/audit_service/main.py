"""Converse AI - Audit Service"""

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

from audit_service.config.settings import settings
from audit_service.infrastructure.persistence.audit_repo_impl import SqlAuditRepository
from audit_service.application.commands.log_action import LogActionCommand, LogActionCommandHandler
from audit_service.api.v1.audit_controller import router as audit_router

logger = structlog.get_logger()

# --- Infrastructure Setup ---

db_manager = DatabaseManager(
    database_url=settings.database_url,
    echo=settings.debug,
)

cache_manager = CacheManager(
    redis_url=settings.redis_url,
    key_prefix="converse:audit",
)

kafka_producer = KafkaProducerManager(
    bootstrap_servers=settings.kafka_bootstrap_servers,
    client_id="audit-service-producer",
)

in_process_bus = InProcessEventBus()
event_bus = KafkaEventBus(
    producer=kafka_producer,
    topic_prefix="converse.audit",
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
    logger.info("audit_service_initializing")
    await db_manager.initialize()
    await cache_manager.initialize()
    await kafka_producer.initialize()
    
    yield
    
    logger.info("audit_service_shutting_down")
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

def get_repo(uow: SqlAlchemyUnitOfWork | None = None) -> SqlAuditRepository:
    session = uow.session if uow else db_manager.session_factory()
    return SqlAuditRepository(session)

# Register Handlers
mediator.register(
    LogActionCommand,
    lambda: LogActionCommandHandler(
        uow=(uow := get_uow()),
        repo=get_repo(uow)
    )
)


# --- API Routes ---

app.include_router(audit_router)
