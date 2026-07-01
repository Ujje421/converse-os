"""Repository interface for User Profile."""

import uuid
from typing import Protocol

from converse_shared.domain.value_objects import Email
from user_service.domain.entities.user_profile import UserProfile


class UserProfileRepository(Protocol):
    """Interface for managing user profiles in persistence."""
    
    async def save(self, profile: UserProfile) -> None:
        """Save a user profile aggregate to the database."""
        ...
        
    async def get_by_id(self, user_id: uuid.UUID) -> UserProfile | None:
        """Retrieve profile by user ID."""
        ...
        
    async def get_by_email(self, email: Email) -> UserProfile | None:
        """Retrieve profile by email address."""
        ...
