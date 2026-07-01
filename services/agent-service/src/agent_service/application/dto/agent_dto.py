"""Agent Service DTOs."""

from pydantic import BaseModel, constr


class LLMSettingsDTO(BaseModel):
    """DTO for LLM Settings."""
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 2048


class CreateAgentRequest(BaseModel):
    """Request DTO for creating an agent."""
    name: constr(min_length=2, max_length=100) # type: ignore
    description: str | None = None
    llm_provider: str
    model_name: str
    system_prompt: str
    settings: LLMSettingsDTO | None = None


class AgentResponse(BaseModel):
    """Response DTO for agent."""
    id: str
    org_id: str
    name: str
    description: str | None
    llm_provider: str
    model_name: str
    system_prompt: str
    settings: LLMSettingsDTO
    is_active: bool
