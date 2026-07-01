"""Register User Command."""

import uuid

import structlog
from pydantic import EmailStr

from converse_shared.application.cqrs import Command, CommandHandler
from converse_shared.application.dto import Result
from converse_shared.domain.exceptions import EntityAlreadyExists, ValidationError
from converse_shared.domain.value_objects import Email
from converse_shared.infrastructure.unit_of_work import UnitOfWork

from auth_service.domain.entities.user_credentials import UserCredentials
from auth_service.domain.value_objects.password import PasswordHash
from auth_service.domain.repositories.credentials_repo import UserCredentialsRepository
from auth_service.domain.events.auth_events import UserRegisteredEvent

logger = structlog.get_logger()


class RegisterCommand(Command[uuid.UUID]):
    """Command to register a new user."""
    email: EmailStr
    password: str


class RegisterCommandHandler(CommandHandler[RegisterCommand, uuid.UUID]):
    """Handler for registering a new user."""

    def __init__(
        self,
        uow: UnitOfWork,
        repo: UserCredentialsRepository,
    ) -> None:
        self.uow = uow
        self.repo = repo

    async def handle(self, command: RegisterCommand) -> Result[uuid.UUID]:
        """Process the registration command."""
        try:
            email_vo = Email(command.email)
            password_vo = PasswordHash.create(command.password)
        except ValueError as e:
            raise ValidationError(message=str(e))

        async with self.uow:
            # Check if email is already taken
            existing = await self.repo.get_by_email(email_vo)
            if existing:
                raise EntityAlreadyExists(message="A user with this email already exists")

            user_id = uuid.uuid4()
            
            # Create domain entity
            credentials = UserCredentials.create(
                user_id=user_id,
                email=email_vo,
                password_hash=password_vo,
            )
            
            # Add Domain Event
            credentials.add_domain_event(
                UserRegisteredEvent(
                    user_id=user_id,
                    email=str(email_vo),
                )
            )

            # Persist
            await self.repo.save(credentials)
            
            # Register entity with UoW for event dispatch
            self.uow.register_aggregate(credentials)
            
            logger.info("user_registered_successfully", user_id=str(user_id))

            return Result.ok(user_id)
