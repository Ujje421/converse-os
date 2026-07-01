"""Repository interface — generic repository pattern for persistence abstraction."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from converse_shared.domain.base_entity import BaseEntity
from converse_shared.domain.value_objects import Pagination

T = TypeVar("T", bound=BaseEntity)


class PaginatedResult(Generic[T]):
    """Paginated query result container."""

    def __init__(
        self,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> None:
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }


class Repository(ABC, Generic[T]):
    """Abstract repository providing CRUD operations for aggregates.

    Implementations live in the infrastructure layer and interact with
    the persistence mechanism (PostgreSQL via SQLAlchemy).

    The repository pattern ensures the domain layer has no knowledge of
    persistence details.
    """

    @abstractmethod
    async def get_by_id(self, entity_id: uuid.UUID) -> T | None:
        """Retrieve an entity by its unique identifier.

        Args:
            entity_id: UUID of the entity.

        Returns:
            The entity if found, None otherwise.
        """
        ...

    @abstractmethod
    async def get_by_id_or_raise(self, entity_id: uuid.UUID) -> T:
        """Retrieve an entity by ID or raise EntityNotFound.

        Args:
            entity_id: UUID of the entity.

        Returns:
            The entity.

        Raises:
            EntityNotFound: If the entity does not exist.
        """
        ...

    @abstractmethod
    async def list(
        self,
        pagination: Pagination | None = None,
        filters: dict[str, Any] | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> PaginatedResult[T]:
        """List entities with pagination, filtering, and sorting.

        Args:
            pagination: Pagination parameters.
            filters: Key-value filters to apply.
            sort_by: Field name to sort by.
            sort_order: Sort direction ('asc' or 'desc').

        Returns:
            PaginatedResult containing matching entities.
        """
        ...

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add a new entity to the repository.

        Args:
            entity: The entity to persist.

        Returns:
            The persisted entity with any generated values.
        """
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: The entity with updated fields.

        Returns:
            The updated entity.
        """
        ...

    @abstractmethod
    async def delete(self, entity_id: uuid.UUID) -> None:
        """Hard-delete an entity by ID.

        Args:
            entity_id: UUID of the entity to delete.
        """
        ...

    @abstractmethod
    async def soft_delete(self, entity_id: uuid.UUID) -> None:
        """Soft-delete an entity by setting is_deleted=True.

        Args:
            entity_id: UUID of the entity to soft-delete.
        """
        ...

    @abstractmethod
    async def exists(self, entity_id: uuid.UUID) -> bool:
        """Check if an entity exists by ID.

        Args:
            entity_id: UUID to check.

        Returns:
            True if the entity exists and is not soft-deleted.
        """
        ...

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities matching the given filters.

        Args:
            filters: Key-value filters to apply.

        Returns:
            Number of matching entities.
        """
        ...


class TenantScopedRepository(Repository[T], ABC):
    """Repository that automatically scopes all queries to the current tenant.

    All operations are implicitly filtered by tenant_id, ensuring strict
    data isolation between tenants.
    """

    @abstractmethod
    async def get_by_id_for_tenant(self, entity_id: uuid.UUID, tenant_id: uuid.UUID) -> T | None:
        """Retrieve an entity by ID within a specific tenant scope."""
        ...

    @abstractmethod
    async def list_for_tenant(
        self,
        tenant_id: uuid.UUID,
        pagination: Pagination | None = None,
        filters: dict[str, Any] | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> PaginatedResult[T]:
        """List entities for a specific tenant."""
        ...
