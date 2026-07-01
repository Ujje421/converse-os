"""Unit tests for Agent Service Domain Entities."""

import uuid

from agent_service.domain.entities.agent import Agent
from agent_service.domain.value_objects.llm_settings import LLMSettings


def test_create_agent():
    """Test agent creation."""
    org_id = uuid.uuid4()
    
    agent = Agent.create(
        org_id=org_id,
        name="Support Bot",
        description="Handles customer support",
        llm_provider="openai",
        model_name="gpt-4",
        system_prompt="You are a helpful assistant.",
    )
    
    assert agent.org_id == org_id
    assert agent.name == "Support Bot"
    assert agent.llm_provider == "openai"
    assert agent.settings.temperature == 0.7  # Default
    assert agent.is_active is True


def test_update_agent_settings():
    """Test updating agent settings."""
    agent = Agent.create(
        org_id=uuid.uuid4(),
        name="Support Bot",
        llm_provider="vertex",
        model_name="gemini-pro",
        system_prompt="You are a helpful assistant.",
    )
    
    new_settings = LLMSettings(temperature=0.2, top_p=0.9, top_k=20, max_tokens=1000)
    agent.update_settings(new_settings)
    
    assert agent.settings.temperature == 0.2
    assert agent.settings.top_k == 20
    
    agent.update_prompt("New prompt")
    assert agent.system_prompt == "New prompt"
