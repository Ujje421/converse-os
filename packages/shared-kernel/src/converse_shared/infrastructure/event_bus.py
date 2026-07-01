"""Event Bus implementation — in-process and Kafka-backed event publishing."""

from __future__ import annotations

import structlog
from typing import Any

from converse_shared.domain.domain_events import DomainEvent, EventBus, EventHandler
from converse_shared.infrastructure.messaging import KafkaMessage, KafkaProducerManager

logger = structlog.get_logger()


class InProcessEventBus(EventBus):
    """In-process event bus for dispatching domain events within a single service.

    Events are dispatched synchronously within the current process.
    Suitable for intra-service event handling.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event to all registered handlers."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(
                    "event_handler_failed",
                    event_type=event_type.__name__,
                    handler=handler.__class__.__name__,
                    error=str(e),
                )

    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple events sequentially."""
        for event in events:
            await self.publish(event)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(
            "event_handler_subscribed",
            event_type=event_type.__name__,
            handler=handler.__class__.__name__,
        )


class KafkaEventBus(EventBus):
    """Kafka-backed event bus for cross-service event publishing.

    Domain events are serialized and published to Kafka topics for
    consumption by other microservices.
    """

    def __init__(
        self,
        producer: KafkaProducerManager,
        topic_prefix: str = "converse.domain",
        in_process_bus: InProcessEventBus | None = None,
    ) -> None:
        self._producer = producer
        self._topic_prefix = topic_prefix
        self._in_process_bus = in_process_bus

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to both in-process handlers and Kafka."""
        # First dispatch to in-process handlers (same service)
        if self._in_process_bus:
            await self._in_process_bus.publish(event)

        # Then publish to Kafka for cross-service consumption
        topic = self._resolve_topic(event)
        message = KafkaMessage(
            topic=topic,
            key=str(event.aggregate_id) if event.aggregate_id else None,
            value={
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "aggregate_id": str(event.aggregate_id) if event.aggregate_id else None,
                "tenant_id": str(event.tenant_id) if event.tenant_id else None,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "occurred_at": event.occurred_at.isoformat(),
                "data": event.model_dump(exclude={"event_id", "event_type", "occurred_at", "aggregate_id", "tenant_id", "correlation_id", "causation_id", "metadata"}),
                "metadata": event.metadata,
            },
            headers={
                "event-type": event.event_type,
                "correlation-id": event.correlation_id or "",
            },
        )

        try:
            await self._producer.send(message)
            logger.info(
                "domain_event_published",
                event_type=event.event_type,
                event_id=str(event.event_id),
                topic=topic,
            )
        except Exception as e:
            logger.error(
                "domain_event_publish_failed",
                event_type=event.event_type,
                error=str(e),
            )
            raise

    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Subscribe is only for in-process handlers. Kafka consumers subscribe separately."""
        if self._in_process_bus:
            self._in_process_bus.subscribe(event_type, handler)

    def _resolve_topic(self, event: DomainEvent) -> str:
        """Resolve the Kafka topic for a domain event based on its type."""
        # Convention: converse.domain.{aggregate_type}.events
        parts = event.event_type.split(".")
        if len(parts) >= 2:
            # Extract service/aggregate from module path
            return f"{self._topic_prefix}.events"
        return f"{self._topic_prefix}.events"
