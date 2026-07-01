"""API Key management — generation, hashing, and validation."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ApiKeyInfo(BaseModel):
    """API Key metadata (stored in database — key itself is NOT stored)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    prefix: str  # First 8 chars of the key (for identification)
    key_hash: str  # SHA-256 hash of the full key
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GeneratedApiKey(BaseModel):
    """Newly generated API key — returned ONCE to the user."""

    key: str  # The full API key (shown only once)
    info: ApiKeyInfo


class ApiKeyManager:
    """API key generation, hashing, and validation.

    API keys follow the format: cvs_{prefix}_{random}
    - Prefix: 8 chars for identification
    - Random: 32 chars of cryptographic randomness
    - Total: ~45 characters

    Only the SHA-256 hash is stored; the raw key is returned once at creation.

    Usage:
        manager = ApiKeyManager()
        generated = manager.generate(name="My Key", tenant_id=..., user_id=...)
        # Show generated.key to user (only time it's visible)

        # Later, validate incoming key
        key_hash = manager.hash_key("cvs_abcd1234_...")
        # Look up key_hash in database
    """

    KEY_PREFIX = "cvs"
    PREFIX_LENGTH = 8
    RANDOM_LENGTH = 32

    def generate(
        self,
        name: str,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        scopes: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> GeneratedApiKey:
        """Generate a new API key.

        Returns:
            GeneratedApiKey with the raw key (shown once) and metadata.
        """
        prefix = secrets.token_hex(self.PREFIX_LENGTH // 2)
        random_part = secrets.token_hex(self.RANDOM_LENGTH // 2)
        raw_key = f"{self.KEY_PREFIX}_{prefix}_{random_part}"

        key_hash = self.hash_key(raw_key)

        info = ApiKeyInfo(
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            tenant_id=tenant_id,
            user_id=user_id,
            scopes=scopes or [],
            expires_at=expires_at,
        )

        return GeneratedApiKey(key=raw_key, info=info)

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Hash an API key with SHA-256."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def extract_prefix(raw_key: str) -> str | None:
        """Extract the prefix from a raw API key for lookup."""
        parts = raw_key.split("_")
        if len(parts) >= 3 and parts[0] == "cvs":
            return parts[1]
        return None

    @staticmethod
    def is_valid_format(raw_key: str) -> bool:
        """Check if a string looks like a valid API key format."""
        parts = raw_key.split("_")
        return len(parts) == 3 and parts[0] == "cvs" and len(parts[1]) == 8

    def validate(self, raw_key: str, stored_hash: str) -> bool:
        """Validate an API key against a stored hash."""
        computed_hash = self.hash_key(raw_key)
        return secrets.compare_digest(computed_hash, stored_hash)
