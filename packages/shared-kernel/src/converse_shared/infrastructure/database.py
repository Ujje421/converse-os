"""Database infrastructure — SQLAlchemy 2.0 async engine, session factory, and tenant-aware base."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, AsyncGenerator

import structlog
from sqlalchemy import MetaData, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, Boolean, Uuid

logger = structlog.get_logger()

# Naming convention for constraints (ensures consistent migration names)
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base with naming conventions."""

    metadata = metadata


class TimestampMixin:
    """Mixin for created_at/updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft-delete support."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TenantMixin:
    """Mixin for multi-tenant entities. Adds tenant_id column."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """Abstract base model combining common columns.

    All service-specific ORM models should inherit from this.
    Provides: id, created_at, updated_at, is_deleted, deleted_at.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )


class TenantBaseModel(BaseModel, TenantMixin):
    """Abstract base model with tenant isolation.

    For models that belong to a specific tenant (organization).
    Automatically includes tenant_id for row-level isolation.
    """

    __abstract__ = True


class DatabaseManager:
    """Manages database connections, engines, and session factories.

    Supports multiple databases (one per service) and provides
    tenant-aware session creation.

    Usage:
        db = DatabaseManager(database_url="postgresql+asyncpg://...")
        await db.initialize()

        async with db.session() as session:
            result = await session.execute(select(User))
    """

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
    ) -> None:
        self._database_url = database_url
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._echo = echo
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._pool_timeout = pool_timeout
        self._pool_recycle = pool_recycle
        self._pool_pre_ping = pool_pre_ping

    async def initialize(self) -> None:
        """Create the async engine and session factory."""
        self._engine = create_async_engine(
            self._database_url,
            echo=self._echo,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            pool_timeout=self._pool_timeout,
            pool_recycle=self._pool_recycle,
            pool_pre_ping=self._pool_pre_ping,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info("database_initialized", url=self._sanitize_url(self._database_url))

    async def close(self) -> None:
        """Close the engine and release all connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("database_closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new database session as an async context manager.

        Commits on success, rolls back on exception.
        """
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def read_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a read-only session (no auto-commit)."""
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")

        session = self._session_factory()
        try:
            yield session
        finally:
            await session.close()

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("DatabaseManager not initialized.")
        return self._engine

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """Remove password from URL for logging."""
        if "@" in url:
            prefix, rest = url.split("@", 1)
            if ":" in prefix:
                parts = prefix.rsplit(":", 1)
                return f"{parts[0]}:***@{rest}"
        return url


def build_database_url(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    driver: str = "asyncpg",
) -> str:
    """Construct a PostgreSQL async database URL."""
    return f"postgresql+{driver}://{user}:{password}@{host}:{port}/{database}"
