"""Repository interface for User Credentials."""

import uuid
from typing import Protocol

from converse_shared.domain.value_objects import Email
from auth_service.domain.entities.user_credentials import UserCredentials


class UserCredentialsRepository(Protocol):
    """Interface for managing user credentials in persistence."""
    
    async def save(self, credentials: UserCredentials) -> None:
        """Save a user credentials aggregate to the database."""
        ...
        
    async def get_by_id(self, user_id: uuid.UUID) -> UserCredentials | None:
        """Retrieve credentials by user ID."""
        ...
        
    async def get_by_email(self, email: Email) -> UserCredentials | None:
        """Retrieve credentials by email address."""
        ...
