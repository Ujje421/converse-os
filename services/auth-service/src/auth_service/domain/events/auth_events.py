"""Domain events for the Auth Service."""

import uuid

from converse_shared.domain.domain_events import DomainEvent


class UserRegisteredEvent(DomainEvent):
    """Fired when a new user registers and credentials are created."""
    user_id: uuid.UUID
    email: str


class UserAuthenticatedEvent(DomainEvent):
    """Fired on successful login."""
    user_id: uuid.UUID
    ip_address: str | None = None
    user_agent: str | None = None


class UserPasswordChangedEvent(DomainEvent):
    """Fired when a user updates their password."""
    user_id: uuid.UUID


class UserAccountLockedEvent(DomainEvent):
    """Fired when an account is locked due to too many failed attempts."""
    user_id: uuid.UUID
    lock_duration_minutes: int
