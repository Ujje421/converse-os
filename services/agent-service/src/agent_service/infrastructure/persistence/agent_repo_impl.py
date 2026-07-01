"""SQLAlchemy implementation of AgentRepository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.domain.entities.agent import Agent
from agent_service.domain.value_objects.llm_settings import LLMSettings
from agent_service.domain.repositories.agent_repo import AgentRepository
from agent_service.infrastructure.persistence.models import AgentModel


class SqlAgentRepository(AgentRepository):
    """SQLAlchemy-based implementation of AgentRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, agent: Agent) -> None:
        """Save an agent aggregate to the database."""
        model = await self.session.get(AgentModel, agent.id)
        
        if not model:
            # Create new
            model = AgentModel(
                id=agent.id,
                org_id=agent.org_id,
                name=agent.name,
                description=agent.description,
                llm_provider=agent.llm_provider,
                model_name=agent.model_name,
                system_prompt=agent.system_prompt,
                settings=agent.settings.model_dump(),
                is_active=agent.is_active,
            )
            self.session.add(model)
        else:
            # Update existing
            model.name = agent.name
            model.description = agent.description
            model.llm_provider = agent.llm_provider
            model.model_name = agent.model_name
            model.system_prompt = agent.system_prompt
            model.settings = agent.settings.model_dump()
            model.is_active = agent.is_active
            
        await self.session.flush()

    async def get_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        """Retrieve agent by ID."""
        model = await self.session.get(AgentModel, agent_id)
        return self._to_entity(model) if model else None

    async def list_by_org(self, org_id: uuid.UUID) -> list[Agent]:
        """List all agents for an organization."""
        stmt = select(AgentModel).where(AgentModel.org_id == org_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: AgentModel) -> Agent:
        """Map SQLAlchemy model to Domain Entity."""
        entity = Agent.reconstitute(
            id=model.id,
            org_id=model.org_id,
            name=model.name,
            description=model.description,
            llm_provider=model.llm_provider,
            model_name=model.model_name,
            system_prompt=model.system_prompt,
            settings=LLMSettings(**model.settings),
            is_active=model.is_active,
        )
        return entity
