"""Converse AI - Auth Service"""

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

from auth_service.config.settings import settings

logger = structlog.get_logger()

# --- Infrastructure Setup ---

db_manager = DatabaseManager(
    database_url=settings.database_url,
    echo=settings.debug,
)

cache_manager = CacheManager(
    redis_url=settings.redis_url,
    key_prefix="converse:auth",
)

kafka_producer = KafkaProducerManager(
    bootstrap_servers=settings.kafka_bootstrap_servers,
    client_id="auth-service-producer",
)

in_process_bus = InProcessEventBus()
event_bus = KafkaEventBus(
    producer=kafka_producer,
    topic_prefix="converse.auth",
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
    # Startup
    logger.info("auth_service_initializing")
    await db_manager.initialize()
    await cache_manager.initialize()
    await kafka_producer.initialize()
    
    yield
    
    # Shutdown
    logger.info("auth_service_shutting_down")
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

from converse_shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from converse_shared.security.jwt import JWTHandler
from auth_service.infrastructure.persistence.credential_repo_impl import SqlUserCredentialsRepository
from auth_service.application.commands.register import RegisterCommand, RegisterCommandHandler
from auth_service.application.commands.login import LoginCommand, LoginCommandHandler
from auth_service.api.v1.auth_controller import router as auth_router

# Initialize JWT Handler
jwt_handler = JWTHandler(
    private_key_path=settings.jwt_private_key_path,
    public_key_path=settings.jwt_public_key_path,
    algorithm=settings.jwt_algorithm,
)

# Factories for DI
def get_uow() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(db_manager.session_factory, event_bus)

def get_repo(uow: SqlAlchemyUnitOfWork) -> SqlUserCredentialsRepository:
    return SqlUserCredentialsRepository(uow.session)

# Register Handlers
mediator.register(
    RegisterCommand,
    lambda: RegisterCommandHandler(
        uow=(uow := get_uow()),
        repo=get_repo(uow)
    )
)

mediator.register(
    LoginCommand,
    lambda: LoginCommandHandler(
        uow=(uow := get_uow()),
        repo=get_repo(uow),
        jwt_handler=jwt_handler
    )
)

# --- API Routes ---

app.include_router(auth_router)

@app.get("/api/v1/auth/me")
async def read_me():
    """Placeholder for /me endpoint."""
    return {"message": "auth service is running"}
