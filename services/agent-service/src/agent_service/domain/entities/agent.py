"""Domain entities for Agent Management."""

from __future__ import annotations

import uuid

from converse_shared.domain.aggregate_root import AggregateRoot
from agent_service.domain.value_objects.llm_settings import LLMSettings


class Agent(AggregateRoot):
    """Aggregate root for a Conversational Agent."""

    org_id: uuid.UUID
    name: str
    description: str | None = None
    llm_provider: str  # vertex, openai, anthropic
    model_name: str
    system_prompt: str
    settings: LLMSettings
    is_active: bool = True

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        name: str,
        llm_provider: str,
        model_name: str,
        system_prompt: str,
        description: str | None = None,
        settings: LLMSettings | None = None,
    ) -> Agent:
        """Create a new agent."""
        return cls(
            org_id=org_id,
            name=name,
            description=description,
            llm_provider=llm_provider,
            model_name=model_name,
            system_prompt=system_prompt,
            settings=settings or LLMSettings(),
        )

    def update_prompt(self, new_prompt: str) -> None:
        """Update the agent's system prompt."""
        self.system_prompt = new_prompt
        self.mark_updated()

    def update_settings(self, new_settings: LLMSettings) -> None:
        """Update the agent's LLM generation settings."""
        self.settings = new_settings
        self.mark_updated()
