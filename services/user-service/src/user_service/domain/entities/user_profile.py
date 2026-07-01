"""Domain entity for User Profile."""

from __future__ import annotations

import uuid
from typing import Any

from converse_shared.domain.aggregate_root import AggregateRoot
from converse_shared.domain.value_objects import Email


class UserProfile(AggregateRoot):
    """Aggregate root for managing user profile information."""

    # Note: user_id is the primary identifier, not id (since it aligns with auth service user_id)
    # Actually, AggregateRoot defines `id: uuid.UUID = field(default_factory=uuid.uuid4)`
    # So we'll map `id` to `user_id` logically.

    email: Email
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    preferences: dict[str, Any]
    timezone: str = "UTC"

    @classmethod
    def create(
        cls,
        user_id: uuid.UUID,
        email: Email,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> UserProfile:
        """Create a new user profile.
        
        Usually called in response to UserRegisteredEvent from Auth Service.
        """
        return cls(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            preferences={},
        )

    def update_profile(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        avatar_url: str | None = None,
        timezone: str | None = None,
    ) -> None:
        """Update basic profile information."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if avatar_url is not None:
            self.avatar_url = avatar_url
        if timezone is not None:
            self.timezone = timezone
            
        self.mark_updated()
        # Events could be emitted here (e.g., ProfileUpdatedEvent)

    def update_preferences(self, new_preferences: dict[str, Any]) -> None:
        """Update user preferences."""
        # Deep merge could go here, for now just simple update
        self.preferences.update(new_preferences)
        self.mark_updated()
