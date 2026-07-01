"""Aggregate Root — DDD pattern with domain event tracking."""

from __future__ import annotations

from converse_shared.domain.base_entity import BaseEntity
from converse_shared.domain.domain_events import DomainEvent


class AggregateRoot(BaseEntity):
    """Aggregate Root extends BaseEntity with domain event tracking.

    Aggregates are the consistency boundaries in DDD. They track domain
    events that occurred during the current unit of work and are dispatched
    after the aggregate is persisted.

    Usage:
        class Order(AggregateRoot):
            def place(self):
                self._register_event(OrderPlaced(order_id=self.id))
    """

    _domain_events: list[DomainEvent] = []

    def model_post_init(self, __context: object) -> None:
        """Initialize the events list after model construction."""
        self._domain_events = []

    def _register_event(self, event: DomainEvent) -> None:
        """Register a domain event to be dispatched after persistence."""
        self._domain_events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """Collect and clear all pending domain events.

        Returns:
            List of domain events that were registered since last collection.
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    @property
    def has_pending_events(self) -> bool:
        """Check if there are pending domain events."""
        return len(self._domain_events) > 0
