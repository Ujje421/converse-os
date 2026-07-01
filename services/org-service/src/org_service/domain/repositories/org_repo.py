"""Repository interface for Organization."""

import uuid
from typing import Protocol

from org_service.domain.entities.organization import Organization


class OrganizationRepository(Protocol):
    """Interface for managing organizations in persistence."""
    
    async def save(self, org: Organization) -> None:
        """Save an organization aggregate to the database."""
        ...
        
    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
        """Retrieve organization by ID."""
        ...
        
    async def get_by_slug(self, slug: str) -> Organization | None:
        """Retrieve organization by slug."""
        ...
