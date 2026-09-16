"""Reusable fixed-window rate limiting primitives."""
from dataclasses import dataclass
from typing import Protocol

import redis.exceptions
from redis.asyncio import Redis


@dataclass(frozen=True)
class RateLimitDecision:
    """Result of checking one fixed-window rate-limit bucket."""

    allowed: bool
    retry_after_seconds: int = 0


class RateLimitBackendError(RuntimeError):
    """Raised when the rate-limit state backend cannot be queried."""


class RateLimitBackend(Protocol):
    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Atomically increment a bucket and return its count and TTL."""


class FixedWindowLimiter:
    """Apply fixed-window allow/deny semantics to a backend bucket."""

    def __init__(self, backend: RateLimitBackend):
        self._backend = backend

    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitDecision:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")

        count, ttl = await self._backend.increment(key, window_seconds)
        if count <= limit:
            return RateLimitDecision(allowed=True)
        return RateLimitDecision(allowed=False, retry_after_seconds=max(1, ttl))


class RedisRateLimitBackend:
    """Redis backend using one atomic Lua operation per bucket increment."""

    _INCREMENT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""

    def __init__(self, redis: Redis):
        self._redis = redis

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        try:
            result = await self._redis.eval(
                self._INCREMENT_SCRIPT,
                1,
                key,
                window_seconds,
            )
        except redis.exceptions.RedisError as exc:
            raise RateLimitBackendError("Rate-limit backend unavailable") from exc

        count, ttl = result
        return int(count), int(ttl)
