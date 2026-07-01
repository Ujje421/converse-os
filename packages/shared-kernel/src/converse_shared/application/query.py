"""CQRS Query infrastructure — queries represent intent to read state."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from converse_shared.domain.value_objects import Pagination

R = TypeVar("R")


class Query(BaseModel):
    """Base class for all queries in the CQRS pattern.

    Queries represent read-only requests for data. They never modify state.

    Attributes:
        query_id: Unique identifier for this query.
        tenant_id: Tenant context for data isolation.
        user_id: The user issuing the query.
        correlation_id: For distributed tracing.
        timestamp: When the query was issued.
        pagination: Optional pagination parameters.
    """

    query_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    correlation_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    pagination: Pagination | None = None


class QueryResult(BaseModel, Generic[R]):
    """Standardized query execution result."""

    success: bool = True
    data: Any = None
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any = None, **metadata: Any) -> QueryResult:
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error_code: str, error_message: str) -> QueryResult:
        return cls(success=False, error_code=error_code, error_message=error_message)


class QueryHandler(ABC, Generic[R]):
    """Abstract handler for processing queries.

    Query handlers are responsible for reading and returning data.
    They should NOT modify any state.
    """

    @abstractmethod
    async def handle(self, query: Query) -> QueryResult[R]:
        """Execute the query and return a result.

        Args:
            query: The query to execute.

        Returns:
            QueryResult with the requested data.
        """
        ...
