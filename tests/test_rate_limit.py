import math

import pytest
import redis.exceptions

from rag_engine.api.rate_limit import (
    FixedWindowLimiter,
    RateLimitBackendError,
    RedisRateLimitBackend,
)


class FakeBackend:
    def __init__(self, clock):
        self.clock = clock
        self.buckets = {}
        self.error = None

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        if self.error is not None:
            raise self.error

        count, expires_at = self.buckets.get(key, (0, self.clock()))
        if self.clock() >= expires_at:
            count = 0
            expires_at = self.clock() + window_seconds

        count += 1
        self.buckets[key] = count, expires_at
        ttl = math.ceil(expires_at - self.clock())
        return count, max(0, ttl)


@pytest.fixture
def clock():
    return [100.0]


@pytest.fixture
def backend(clock):
    return FakeBackend(lambda: clock[0])


@pytest.mark.asyncio
async def test_allows_requests_through_limit(backend):
    limiter = FixedWindowLimiter(backend)

    first = await limiter.check("bucket", limit=2, window_seconds=60)
    second = await limiter.check("bucket", limit=2, window_seconds=60)

    assert first.allowed
    assert second.allowed
    assert first.retry_after_seconds == second.retry_after_seconds == 0


@pytest.mark.asyncio
async def test_denies_after_limit_with_remaining_ttl(backend, clock):
    limiter = FixedWindowLimiter(backend)

    assert (await limiter.check("bucket", limit=2, window_seconds=60)).allowed
    assert (await limiter.check("bucket", limit=2, window_seconds=60)).allowed
    decision = await limiter.check("bucket", limit=2, window_seconds=60)

    assert not decision.allowed
    assert decision.retry_after_seconds == 60
    clock[0] += 12.25
    decision = await limiter.check("bucket", limit=2, window_seconds=60)
    assert decision.retry_after_seconds == 48


@pytest.mark.asyncio
async def test_expired_window_starts_again(backend, clock):
    limiter = FixedWindowLimiter(backend)

    await limiter.check("bucket", limit=1, window_seconds=10)
    assert not (await limiter.check("bucket", limit=1, window_seconds=10)).allowed

    clock[0] += 10
    decision = await limiter.check("bucket", limit=1, window_seconds=10)

    assert decision.allowed
    assert decision.retry_after_seconds == 0


@pytest.mark.asyncio
async def test_keys_are_isolated(backend):
    limiter = FixedWindowLimiter(backend)

    assert (await limiter.check("one", limit=1, window_seconds=60)).allowed
    assert (await limiter.check("two", limit=1, window_seconds=60)).allowed
    assert not (await limiter.check("one", limit=1, window_seconds=60)).allowed
    assert (await limiter.check("two", limit=1, window_seconds=60)).retry_after_seconds == 60


@pytest.mark.asyncio
async def test_backend_errors_are_propagated(backend):
    backend.error = RateLimitBackendError("backend unavailable")
    limiter = FixedWindowLimiter(backend)

    with pytest.raises(RateLimitBackendError, match="backend unavailable"):
        await limiter.check("bucket", limit=1, window_seconds=60)


@pytest.mark.asyncio
async def test_redis_errors_are_wrapped_but_programming_errors_are_not():
    class FailingRedis:
        def __init__(self, error):
            self.error = error

        async def eval(self, *args):
            raise self.error

    with pytest.raises(RateLimitBackendError, match="backend unavailable"):
        await RedisRateLimitBackend(FailingRedis(redis.exceptions.ConnectionError())).increment(
            "bucket", 60
        )

    with pytest.raises(TypeError, match="bad eval call"):
        await RedisRateLimitBackend(FailingRedis(TypeError("bad eval call"))).increment(
            "bucket", 60
        )


@pytest.mark.asyncio
async def test_invalid_limits_are_rejected(backend):
    limiter = FixedWindowLimiter(backend)

    with pytest.raises(ValueError, match="limit"):
        await limiter.check("bucket", limit=0, window_seconds=60)
    with pytest.raises(ValueError, match="window_seconds"):
        await limiter.check("bucket", limit=1, window_seconds=0)
