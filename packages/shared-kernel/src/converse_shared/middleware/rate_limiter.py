"""Rate limiting middleware using Redis sliding window."""

import time
from typing import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from converse_shared.infrastructure.cache import CacheManager
from converse_shared.domain.exceptions import RateLimitExceeded

logger = structlog.get_logger()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding window rate limiter."""

    def __init__(
        self,
        app,
        cache: CacheManager,
        default_limit: int = 100,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.cache = cache
        self.default_limit = default_limit
        self.window_seconds = window_seconds

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip rate limiting for internal/health endpoints
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        # Identify client by IP or API Key or User ID
        client_id = request.headers.get("X-User-ID") or request.client.host if request.client else "unknown"
        
        if await self._is_rate_limited(client_id):
            raise RateLimitExceeded(
                limit=self.default_limit,
                window_seconds=self.window_seconds,
                retry_after=self.window_seconds,
            )

        response = await call_next(request)
        return response
        
    async def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded the limit using Redis sliding window."""
        now = int(time.time())
        window_start = now - self.window_seconds
        key = f"rate_limit:{client_id}"
        
        try:
            redis = self.cache.client
            async with redis.pipeline(transaction=True) as pipe:
                # Remove old requests
                pipe.zremrangebyscore(key, 0, window_start)
                # Count requests in window
                pipe.zcard(key)
                # Add current request
                pipe.zadd(key, {str(now): now})
                # Set TTL to clean up old keys
                pipe.expire(key, self.window_seconds)
                
                results = await pipe.execute()
                
            request_count = results[1]
            return request_count >= self.default_limit
            
        except Exception as e:
            # Fail open if Redis is down
            logger.error("rate_limiter_error", error=str(e))
            return False
