"""Domain events for Organization Management."""

import uuid
from converse_shared.domain.domain_events import DomainEvent


class OrganizationCreatedEvent(DomainEvent):
    """Fired when a new organization is created."""
    org_id: uuid.UUID
    name: str
    owner_id: uuid.UUID


class OrganizationMemberAddedEvent(DomainEvent):
    """Fired when a user is added to an organization."""
    org_id: uuid.UUID
    user_id: uuid.UUID
    role: str
