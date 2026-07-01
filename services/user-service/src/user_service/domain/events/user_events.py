"""User Service domain events."""

import uuid
from converse_shared.domain.domain_events import DomainEvent


class UserProfileUpdatedEvent(DomainEvent):
    """Fired when a user profile is updated."""
    user_id: uuid.UUID


class UserPreferencesUpdatedEvent(DomainEvent):
    """Fired when a user updates their preferences."""
    user_id: uuid.UUID
