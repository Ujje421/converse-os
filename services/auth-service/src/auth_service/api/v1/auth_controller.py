"""Auth Service Controllers."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request

from converse_shared.application.dto import ApiResponse
from converse_shared.application.mediator import Mediator

from auth_service.application.dto.auth_dto import LoginRequest, RegisterRequest, TokenResponse
from auth_service.application.commands.login import LoginCommand
from auth_service.application.commands.register import RegisterCommand
from auth_service.main import mediator  # Import the global mediator instance

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse[dict])
async def register(request: RegisterRequest, req: Request):
    """Register a new user."""
    command = RegisterCommand(
        email=request.email,
        password=request.password,
    )
    result = await mediator.send(command)
    
    if not result.success:
        # Let the ErrorHandlerMiddleware handle it if it raised an exception, 
        # or we manually return a bad request if handled internally.
        pass
        
    return ApiResponse.created(data={"user_id": str(result.data)})


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(request: LoginRequest, req: Request):
    """Authenticate a user and return JWT tokens."""
    command = LoginCommand(
        email=request.email,
        password=request.password,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )
    
    result = await mediator.send(command)
    
    if not result.success:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    return ApiResponse.ok(data=result.data)
