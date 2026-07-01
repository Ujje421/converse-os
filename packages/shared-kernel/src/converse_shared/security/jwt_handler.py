"""JWT Handler — RS256 token creation, validation, and refresh."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str  # User ID
    tenant_id: str | None = None
    org_id: str | None = None
    email: str | None = None
    roles: list[str] = []
    permissions: list[str] = []
    token_type: str = "access"  # "access" or "refresh"
    jti: str = ""  # JWT ID for revocation tracking
    iat: int = 0  # Issued at
    exp: int = 0  # Expiration
    iss: str = "converse"  # Issuer


class TokenPair(BaseModel):
    """Access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds until access token expires


class JWTHandler:
    """RS256 JWT handler for token creation and validation.

    Uses asymmetric keys (RS256) for production security:
    - Private key: used by Auth Service to sign tokens
    - Public key: distributed to all services for validation

    Usage:
        handler = JWTHandler(
            private_key_path="/keys/jwt-private.pem",
            public_key_path="/keys/jwt-public.pem",
        )
        pair = handler.create_token_pair(user_id=..., tenant_id=..., roles=[...])
        payload = handler.validate_token(pair.access_token)
    """

    def __init__(
        self,
        private_key_path: str | None = None,
        public_key_path: str | None = None,
        private_key: str | None = None,
        public_key: str | None = None,
        algorithm: str = "RS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 30,
        issuer: str = "converse",
    ) -> None:
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days
        self._issuer = issuer

        # Load keys
        self._private_key = private_key
        self._public_key = public_key

        if private_key_path and Path(private_key_path).exists():
            self._private_key = Path(private_key_path).read_text()
        if public_key_path and Path(public_key_path).exists():
            self._public_key = Path(public_key_path).read_text()

    def create_access_token(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
        org_id: uuid.UUID | None = None,
        email: str | None = None,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a signed JWT access token.

        Args:
            user_id: The user's UUID.
            tenant_id: The tenant's UUID for multi-tenancy.
            org_id: The organization's UUID.
            email: User's email.
            roles: List of role names.
            permissions: List of permission strings.
            extra_claims: Additional JWT claims.

        Returns:
            Encoded JWT string.
        """
        if not self._private_key:
            raise RuntimeError("Private key not configured for token signing.")

        now = datetime.now(UTC)
        expire = now + timedelta(minutes=self._access_token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "org_id": str(org_id) if org_id else None,
            "email": email,
            "roles": roles or [],
            "permissions": permissions or [],
            "token_type": "access",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "iss": self._issuer,
        }

        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self._private_key, algorithm=self._algorithm)
        logger.debug("access_token_created", user_id=str(user_id), expires_at=expire.isoformat())
        return token

    def create_refresh_token(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
    ) -> str:
        """Create a signed JWT refresh token with extended expiration."""
        if not self._private_key:
            raise RuntimeError("Private key not configured for token signing.")

        now = datetime.now(UTC)
        expire = now + timedelta(days=self._refresh_token_expire_days)

        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "token_type": "refresh",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "iss": self._issuer,
        }

        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def create_token_pair(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
        org_id: uuid.UUID | None = None,
        email: str | None = None,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
    ) -> TokenPair:
        """Create an access + refresh token pair."""
        access_token = self.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            org_id=org_id,
            email=email,
            roles=roles,
            permissions=permissions,
        )
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_token_expire_minutes * 60,
        )

    def validate_token(self, token: str) -> TokenPayload:
        """Validate and decode a JWT token.

        Args:
            token: The encoded JWT string.

        Returns:
            Decoded TokenPayload.

        Raises:
            jwt.ExpiredSignatureError: If the token has expired.
            jwt.InvalidTokenError: If the token is invalid.
        """
        if not self._public_key:
            raise RuntimeError("Public key not configured for token validation.")

        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "require": ["sub", "exp", "iat", "jti"],
                },
            )
            return TokenPayload(**payload)

        except jwt.ExpiredSignatureError:
            logger.warning("token_expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning("token_invalid", error=str(e))
            raise

    def decode_without_verification(self, token: str) -> dict[str, Any]:
        """Decode a token without verification (for debugging/logging only)."""
        return jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=[self._algorithm],
        )

    def get_jti(self, token: str) -> str:
        """Extract the JTI (JWT ID) from a token for revocation tracking."""
        payload = self.decode_without_verification(token)
        return payload.get("jti", "")
