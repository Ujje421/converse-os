"""Agent Service Controllers."""

import structlog
from fastapi import APIRouter, Depends, Request

from converse_shared.application.dto import ApiResponse
from converse_shared.security.tenant_context import TenantContext

from agent_service.application.dto.agent_dto import CreateAgentRequest, AgentResponse
from agent_service.application.commands.create_agent import CreateAgentCommand
from agent_service.main import mediator  # Global mediator instance

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


@router.post("", response_model=ApiResponse[AgentResponse])
async def create_agent(request: CreateAgentRequest):
    """Create a new agent."""
    org_id = TenantContext.get_tenant_id()
    if not org_id:
        from converse_shared.domain.exceptions import AuthorizationError
        raise AuthorizationError("Tenant ID (org) not found in context.")
        
    command = CreateAgentCommand(
        org_id=org_id,
        name=request.name,
        description=request.description,
        llm_provider=request.llm_provider,
        model_name=request.model_name,
        system_prompt=request.system_prompt,
        settings=request.settings,
    )
    result = await mediator.send(command)
    return ApiResponse.created(data=result.data)
