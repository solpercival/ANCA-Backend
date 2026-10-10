"""Reusable fixed-window rate limiting primitives.

Each limited route counts requests in two buckets per window: one per client IP
and one per account tier. The window's counter lives in Redis (one atomic Lua
call per request), so limits hold across orchestrator replicas.
"""

from dataclasses import dataclass
from typing import Protocol

import redis.exceptions
from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis

from rag_engine.api.errors import RateLimitUnavailable
from rag_engine.auth.dependencies import current_principal
from rag_engine.auth.tiers import Principal
from rag_engine.config import get_settings


@dataclass(frozen=True)
class RateLimitDecision:
    """Result of checking one fixed-window rate-limit bucket."""

    allowed: bool
    retry_after_seconds: int = 0


class RateLimitBackendError(RuntimeError):
    """Raised when the rate-limit state backend cannot be queried."""


class RateLimitBackend(Protocol):
    """Shared counter storage for rate-limit buckets (Redis in production, a fake in tests)."""

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Atomically increment a bucket and return its count and TTL."""


class FixedWindowLimiter:
    """Apply fixed-window allow/deny semantics to a backend bucket."""

    def __init__(self, backend: RateLimitBackend):
        self._backend = backend

    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitDecision:
        """Count this request in `key`'s bucket; deny once the window holds more than `limit`.

        A denial carries the seconds left in the window, for the Retry-After header.
        """
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")

        count, ttl = await self._backend.increment(key, window_seconds)
        if count <= limit:
            return RateLimitDecision(allowed=True)
        if ttl < 0:
            raise RateLimitBackendError("Rate-limit bucket has no valid TTL")
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
        """Add one to `key` and return (count, seconds until the window resets). The
        first request in a window starts its expiry. Raises RateLimitBackendError if
        Redis fails."""
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


def rate_limit_dependency(route_name: str, ip_limit_setting: str, tier_limit_setting: str):
    """Build an authenticated FastAPI dependency for one route's buckets.

    ip_limit_setting / tier_limit_setting name the Settings fields holding each
    bucket's limit. Behaviour: no Redis configured -> requests are not limited;
    over a limit -> 429 with Retry-After; Redis errors -> 503 rate_limit_unavailable
    (fails closed rather than letting unlimited traffic through).
    """

    async def enforce_rate_limit(
        request: Request,
        principal: Principal = Depends(current_principal),
    ) -> None:
        settings = get_settings()
        backend = getattr(request.app.state, "rate_limit_backend", None)
        if backend is None:
            redis_client = getattr(request.app.state, "redis", None)
            if redis_client is not None:
                backend = RedisRateLimitBackend(redis_client)
                request.app.state.rate_limit_backend = backend
        if backend is None:
            return

        limiter = FixedWindowLimiter(backend)
        client_ip = request.client.host if request.client else "unknown"
        buckets = (
            (f"rate-limit:{route_name}:ip:{client_ip}", getattr(settings, ip_limit_setting)),
            (
                f"rate-limit:{route_name}:tier:{principal.tier}",
                getattr(settings, tier_limit_setting),
            ),
        )
        try:
            for key, limit in buckets:
                decision = await limiter.check(key, limit, settings.rate_limit_window_seconds)
                if not decision.allowed:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded",
                        headers={"Retry-After": str(decision.retry_after_seconds)},
                    )
        except RateLimitBackendError as exc:
            raise RateLimitUnavailable() from exc

    return enforce_rate_limit
