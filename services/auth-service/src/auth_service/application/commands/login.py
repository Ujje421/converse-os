"""Login Command and JWT Generation."""

from __future__ import annotations

import time

import structlog
from pydantic import EmailStr

from converse_shared.application.cqrs import Command, CommandHandler
from converse_shared.application.dto import Result
from converse_shared.domain.exceptions import AuthorizationError, ValidationError
from converse_shared.domain.value_objects import Email
from converse_shared.infrastructure.unit_of_work import UnitOfWork
from converse_shared.security.jwt import JWTHandler

from auth_service.application.dto.auth_dto import TokenResponse
from auth_service.domain.repositories.credentials_repo import UserCredentialsRepository
from auth_service.domain.events.auth_events import UserAuthenticatedEvent, UserAccountLockedEvent
from auth_service.config.settings import settings

logger = structlog.get_logger()


class LoginCommand(Command[TokenResponse]):
    """Command to authenticate a user."""
    email: EmailStr
    password: str
    ip_address: str | None = None
    user_agent: str | None = None


class LoginCommandHandler(CommandHandler[LoginCommand, TokenResponse]):
    """Handler for user login."""

    def __init__(
        self,
        uow: UnitOfWork,
        repo: UserCredentialsRepository,
        jwt_handler: JWTHandler,
    ) -> None:
        self.uow = uow
        self.repo = repo
        self.jwt_handler = jwt_handler

    async def handle(self, command: LoginCommand) -> Result[TokenResponse]:
        """Process the login command."""
        try:
            email_vo = Email(command.email)
        except ValueError as e:
            raise ValidationError(message=str(e))

        async with self.uow:
            credentials = await self.repo.get_by_email(email_vo)
            
            if not credentials or not credentials.password_hash:
                # Use same error to prevent username enumeration
                raise AuthorizationError(message="Invalid credentials")
                
            if not credentials.is_active:
                raise AuthorizationError(message="Account is disabled")

            if credentials.is_locked():
                raise AuthorizationError(message="Account is locked due to too many failed attempts")

            # Verify Password
            if not credentials.password_hash.verify(command.password):
                credentials.record_failed_login()
                await self.repo.save(credentials)
                self.uow.register_aggregate(credentials)
                
                if credentials.is_locked():
                    credentials.add_domain_event(
                        UserAccountLockedEvent(
                            user_id=credentials.user_id,
                            lock_duration_minutes=15,
                        )
                    )
                    logger.warning("account_locked", user_id=str(credentials.user_id))
                    
                raise AuthorizationError(message="Invalid credentials")

            # Success
            credentials.record_successful_login()
            credentials.add_domain_event(
                UserAuthenticatedEvent(
                    user_id=credentials.user_id,
                    ip_address=command.ip_address,
                    user_agent=command.user_agent,
                )
            )
            await self.repo.save(credentials)
            self.uow.register_aggregate(credentials)

            # Generate Tokens
            access_token = self.jwt_handler.create_access_token(
                user_id=credentials.user_id,
                tenant_id=None,  # Or default tenant if applicable
                roles=[],  # Roles would typically be fetched from a user/RBAC service
                expires_minutes=settings.jwt_access_token_expire_minutes,
            )
            
            refresh_token = self.jwt_handler.create_refresh_token(
                user_id=credentials.user_id,
                expires_days=settings.jwt_refresh_token_expire_days,
            )
            
            logger.info("user_login_success", user_id=str(credentials.user_id))
            
            response = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.jwt_access_token_expire_minutes * 60,
            )
            
            return Result.ok(response)
