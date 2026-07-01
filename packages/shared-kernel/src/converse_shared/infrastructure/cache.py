"""Redis cache infrastructure — tenant-scoped caching with serialization."""

from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from redis.asyncio import ConnectionPool, Redis

logger = structlog.get_logger()


class CacheManager:
    """Redis-based cache manager with tenant-scoped keys and JSON serialization.

    Provides a high-level interface for caching with automatic key prefixing,
    TTL management, and structured logging.

    Usage:
        cache = CacheManager(redis_url="redis://localhost:6379/0")
        await cache.initialize()

        # Tenant-scoped caching
        await cache.set("user:123", user_data, tenant_id=tenant, ttl=300)
        data = await cache.get("user:123", tenant_id=tenant)
    """

    DEFAULT_TTL = 300  # 5 minutes
    KEY_PREFIX = "converse"

    def __init__(
        self,
        redis_url: str,
        key_prefix: str = KEY_PREFIX,
        default_ttl: int = DEFAULT_TTL,
        max_connections: int = 50,
        decode_responses: bool = True,
    ) -> None:
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._default_ttl = default_ttl
        self._max_connections = max_connections
        self._decode_responses = decode_responses
        self._redis: Redis | None = None
        self._pool: ConnectionPool | None = None

    async def initialize(self) -> None:
        """Initialize the Redis connection pool."""
        self._pool = ConnectionPool.from_url(
            self._redis_url,
            max_connections=self._max_connections,
            decode_responses=self._decode_responses,
        )
        self._redis = Redis(connection_pool=self._pool)
        logger.info("cache_initialized", url=self._sanitize_url(self._redis_url))

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._redis:
            await self._redis.aclose()
        if self._pool:
            await self._pool.disconnect()
        logger.info("cache_closed")

    @property
    def client(self) -> Redis:
        """Get the raw Redis client for advanced operations."""
        if self._redis is None:
            raise RuntimeError("CacheManager not initialized. Call initialize() first.")
        return self._redis

    def _build_key(self, key: str, tenant_id: uuid.UUID | None = None) -> str:
        """Build a namespaced, tenant-scoped cache key."""
        parts = [self._key_prefix]
        if tenant_id:
            parts.append(f"t:{tenant_id}")
        parts.append(key)
        return ":".join(parts)

    async def get(
        self,
        key: str,
        tenant_id: uuid.UUID | None = None,
    ) -> Any | None:
        """Get a cached value by key.

        Args:
            key: Cache key.
            tenant_id: Optional tenant scope.

        Returns:
            Deserialized value or None if not found.
        """
        full_key = self._build_key(key, tenant_id)
        value = await self.client.get(full_key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(
        self,
        key: str,
        value: Any,
        tenant_id: uuid.UUID | None = None,
        ttl: int | None = None,
    ) -> None:
        """Set a cached value with optional TTL.

        Args:
            key: Cache key.
            value: Value to cache (will be JSON-serialized).
            tenant_id: Optional tenant scope.
            ttl: Time-to-live in seconds (defaults to DEFAULT_TTL).
        """
        full_key = self._build_key(key, tenant_id)
        serialized = json.dumps(value, default=str)
        await self.client.set(full_key, serialized, ex=ttl or self._default_ttl)

    async def delete(self, key: str, tenant_id: uuid.UUID | None = None) -> bool:
        """Delete a cached value."""
        full_key = self._build_key(key, tenant_id)
        result = await self.client.delete(full_key)
        return result > 0

    async def exists(self, key: str, tenant_id: uuid.UUID | None = None) -> bool:
        """Check if a key exists in cache."""
        full_key = self._build_key(key, tenant_id)
        return bool(await self.client.exists(full_key))

    async def increment(
        self,
        key: str,
        amount: int = 1,
        tenant_id: uuid.UUID | None = None,
    ) -> int:
        """Atomically increment a counter."""
        full_key = self._build_key(key, tenant_id)
        return await self.client.incrby(full_key, amount)

    async def set_with_nx(
        self,
        key: str,
        value: Any,
        ttl: int,
        tenant_id: uuid.UUID | None = None,
    ) -> bool:
        """Set a value only if the key does not exist (for distributed locks)."""
        full_key = self._build_key(key, tenant_id)
        serialized = json.dumps(value, default=str)
        result = await self.client.set(full_key, serialized, ex=ttl, nx=True)
        return result is not None

    async def get_many(
        self,
        keys: list[str],
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Get multiple cached values in a single round-trip."""
        full_keys = [self._build_key(k, tenant_id) for k in keys]
        values = await self.client.mget(full_keys)
        result = {}
        for key, value in zip(keys, values, strict=False):
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
        return result

    async def delete_pattern(
        self,
        pattern: str,
        tenant_id: uuid.UUID | None = None,
    ) -> int:
        """Delete all keys matching a pattern (use sparingly)."""
        full_pattern = self._build_key(pattern, tenant_id)
        deleted = 0
        async for key in self.client.scan_iter(match=full_pattern):
            await self.client.delete(key)
            deleted += 1
        return deleted

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            result = await self.client.ping()
            return result is True
        except Exception:
            return False

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """Remove password from URL for logging."""
        if "@" in url:
            prefix, rest = url.split("@", 1)
            if ":" in prefix:
                parts = prefix.rsplit(":", 1)
                return f"{parts[0]}:***@{rest}"
        return url
