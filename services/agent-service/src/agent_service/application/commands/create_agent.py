"""Create Agent Command."""

import uuid

import structlog

from converse_shared.application.cqrs import Command, CommandHandler
from converse_shared.application.dto import Result
from converse_shared.infrastructure.unit_of_work import UnitOfWork

from agent_service.domain.entities.agent import Agent
from agent_service.domain.value_objects.llm_settings import LLMSettings
from agent_service.domain.repositories.agent_repo import AgentRepository
from agent_service.domain.events.agent_events import AgentCreatedEvent
from agent_service.application.dto.agent_dto import AgentResponse, LLMSettingsDTO

logger = structlog.get_logger()


class CreateAgentCommand(Command[AgentResponse]):
    """Command to create a new agent."""
    org_id: uuid.UUID
    name: str
    description: str | None
    llm_provider: str
    model_name: str
    system_prompt: str
    settings: LLMSettingsDTO | None


class CreateAgentCommandHandler(CommandHandler[CreateAgentCommand, AgentResponse]):
    """Handler for creating an agent."""

    def __init__(
        self,
        uow: UnitOfWork,
        repo: AgentRepository,
    ) -> None:
        self.uow = uow
        self.repo = repo

    async def handle(self, command: CreateAgentCommand) -> Result[AgentResponse]:
        """Process the create agent command."""
        async with self.uow:
            settings_vo = None
            if command.settings:
                settings_vo = LLMSettings(
                    temperature=command.settings.temperature,
                    top_p=command.settings.top_p,
                    top_k=command.settings.top_k,
                    max_tokens=command.settings.max_tokens,
                )
                
            agent = Agent.create(
                org_id=command.org_id,
                name=command.name,
                description=command.description,
                llm_provider=command.llm_provider,
                model_name=command.model_name,
                system_prompt=command.system_prompt,
                settings=settings_vo,
            )
            
            agent.add_domain_event(
                AgentCreatedEvent(
                    agent_id=agent.id,
                    org_id=command.org_id,
                    name=agent.name,
                )
            )

            await self.repo.save(agent)
            self.uow.register_aggregate(agent)
            
            logger.info("agent_created", agent_id=str(agent.id), org_id=str(command.org_id))
            
            response = AgentResponse(
                id=str(agent.id),
                org_id=str(agent.org_id),
                name=agent.name,
                description=agent.description,
                llm_provider=agent.llm_provider,
                model_name=agent.model_name,
                system_prompt=agent.system_prompt,
                settings=LLMSettingsDTO(
                    temperature=agent.settings.temperature,
                    top_p=agent.settings.top_p,
                    top_k=agent.settings.top_k,
                    max_tokens=agent.settings.max_tokens,
                ),
                is_active=agent.is_active,
            )

            return Result.ok(response)
