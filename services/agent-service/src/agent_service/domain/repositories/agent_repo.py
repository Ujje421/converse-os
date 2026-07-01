"""Repository interface for Agent."""

import uuid
from typing import Protocol

from agent_service.domain.entities.agent import Agent


class AgentRepository(Protocol):
    """Interface for managing agents in persistence."""
    
    async def save(self, agent: Agent) -> None:
        """Save an agent aggregate to the database."""
        ...
        
    async def get_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        """Retrieve agent by ID."""
        ...
        
    async def list_by_org(self, org_id: uuid.UUID) -> list[Agent]:
        """List all agents for an organization."""
        ...
