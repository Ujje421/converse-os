"""Domain Events — base event class and event bus interface."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events.

    Domain events represent something that happened in the domain that
    other parts of the system may need to react to. They are immutable
    records of state changes.

    Attributes:
        event_id: Unique identifier for this event instance.
        event_type: Qualified name of the event class.
        occurred_at: UTC timestamp when the event occurred.
        aggregate_id: ID of the aggregate that raised the event.
        tenant_id: ID of the tenant context in which the event occurred.
        correlation_id: ID for tracing related operations across services.
        causation_id: ID of the event or command that caused this event.
        metadata: Additional metadata for the event.
    """

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str = Field(default="")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: uuid.UUID | None = None
    tenant_id: uuid.UUID | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: object) -> None:
        """Set event_type to the qualified class name if not provided."""
        if not self.event_type:
            self.event_type = f"{self.__class__.__module__}.{self.__class__.__name__}"


class EventHandler(ABC):
    """Interface for domain event handlers."""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event."""
        ...


class EventBus(ABC):
    """Interface for publishing and subscribing to domain events.

    Implementations may be in-process (for same-service events) or
    distributed (via Kafka for cross-service events).
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event."""
        ...

    @abstractmethod
    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events atomically."""
        ...

    @abstractmethod
    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        ...
