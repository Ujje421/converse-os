"""CQRS Command infrastructure — commands represent intent to change state."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

R = TypeVar("R")


class Command(BaseModel):
    """Base class for all commands in the CQRS pattern.

    Commands represent the intent to change the system state. They are
    validated, authorized, and then executed by their corresponding handler.

    Attributes:
        command_id: Unique identifier for idempotency.
        tenant_id: Tenant context for multi-tenant isolation.
        user_id: The user issuing the command.
        correlation_id: For distributed tracing across services.
        timestamp: When the command was issued.
    """

    command_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    correlation_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CommandResult(BaseModel, Generic[R]):
    """Standardized command execution result.

    Attributes:
        success: Whether the command executed successfully.
        data: The result data (if successful).
        error_code: Machine-readable error code (if failed).
        error_message: Human-readable error message (if failed).
        metadata: Additional response metadata.
    """

    success: bool = True
    data: Any = None
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any = None, **metadata: Any) -> CommandResult:
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error_code: str, error_message: str, **metadata: Any) -> CommandResult:
        return cls(
            success=False,
            error_code=error_code,
            error_message=error_message,
            metadata=metadata,
        )


class CommandHandler(ABC, Generic[R]):
    """Abstract handler for processing commands.

    Each command type has exactly one handler. Handlers contain the
    application logic for executing the command, coordinating between
    domain objects and infrastructure.
    """

    @abstractmethod
    async def handle(self, command: Command) -> CommandResult[R]:
        """Execute the command and return a result.

        Args:
            command: The command to execute.

        Returns:
            CommandResult indicating success or failure.
        """
        ...
