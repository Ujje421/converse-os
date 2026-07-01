"""Domain events for Agent Management."""

import uuid
from converse_shared.domain.domain_events import DomainEvent


class AgentCreatedEvent(DomainEvent):
    """Fired when a new agent is created."""
    agent_id: uuid.UUID
    org_id: uuid.UUID
    name: str


class AgentPromptUpdatedEvent(DomainEvent):
    """Fired when an agent's prompt is updated."""
    agent_id: uuid.UUID
    org_id: uuid.UUID
