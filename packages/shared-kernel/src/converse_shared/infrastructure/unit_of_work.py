"""Unit of Work — transactional boundary with domain event dispatch."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from converse_shared.domain.aggregate_root import AggregateRoot
from converse_shared.domain.domain_events import EventBus

logger = structlog.get_logger()


class UnitOfWork(ABC):
    """Abstract Unit of Work — defines the transactional boundary.

    The Unit of Work pattern ensures that all changes within a business
    transaction are committed or rolled back atomically, and domain events
    are dispatched only after successful commit.

    Usage:
        async with uow:
            user = await uow.users.get_by_id(user_id)
            user.update_email(new_email)
            await uow.users.update(user)
            uow.register_events(user)
            await uow.commit()
        # Events are dispatched after commit
    """

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork:
        ...

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction and dispatch domain events."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        ...

    def register_events(self, aggregate: AggregateRoot) -> None:
        """Collect domain events from an aggregate for post-commit dispatch."""
        events = aggregate.collect_events()
        self._pending_events.extend(events)


class SqlAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy-based Unit of Work implementation.

    Manages a database session and dispatches domain events via the
    EventBus after successful commit.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_bus: EventBus | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._session: AsyncSession | None = None
        self._pending_events: list[Any] = []

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self._pending_events = []
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
            logger.warning(
                "uow_rollback",
                exc_type=exc_type.__name__ if exc_type else None,
            )
        if self._session:
            await self._session.close()
        self._session = None

    @property
    def session(self) -> AsyncSession:
        """Get the current session."""
        if self._session is None:
            raise RuntimeError("UnitOfWork not started. Use 'async with uow:'")
        return self._session

    async def commit(self) -> None:
        """Commit the transaction and dispatch pending domain events."""
        if self._session is None:
            raise RuntimeError("UnitOfWork not started.")

        try:
            await self._session.commit()
            logger.debug("uow_committed")

            # Dispatch events after successful commit
            if self._event_bus and self._pending_events:
                await self._event_bus.publish_many(self._pending_events)
                logger.debug(
                    "uow_events_dispatched",
                    event_count=len(self._pending_events),
                )
                self._pending_events.clear()

        except Exception as e:
            await self.rollback()
            logger.error("uow_commit_failed", error=str(e))
            raise

    async def rollback(self) -> None:
        """Rollback the transaction and discard pending events."""
        if self._session:
            await self._session.rollback()
        self._pending_events.clear()
        logger.debug("uow_rolled_back")
