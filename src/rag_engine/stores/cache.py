"""Process-wide Redis clients.

Two clients share the same settings:
- a synchronous pool (get_cache_conn) for blocking callers, which must run in a
  worker thread when on the request path (the session store does this);
- an async client (get_cache_client) for request-path callers that can await
  Redis directly (the rate limiter, the readiness check).
Both return None / yield None before init_cache_pool, so callers can degrade.
"""
from redis import ConnectionPool, Redis
from redis.asyncio import Redis as AsyncRedis
from contextlib import contextmanager
from rag_engine.config import get_settings

# sync pool for the blocking callers (session store, search cache);
# async client for request-path callers (rate limiter, health check)
_cache_pool: ConnectionPool | None = None
_async_client: AsyncRedis | None = None

def init_cache_pool() -> None:
    """Create both clients from settings. Called once at app startup; connects lazily."""
    global _cache_pool, _async_client
    settings = get_settings()
    _cache_pool = ConnectionPool(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
        max_connections=100,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    _async_client = AsyncRedis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
        max_connections=100,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )

def get_cache_client() -> AsyncRedis | None:
    """The async client, or None before init_cache_pool."""
    return _async_client

async def close_cache_pool() -> None:
    """Close both clients at shutdown."""
    global _async_client
    if _async_client:
        await _async_client.aclose()
        _async_client = None
    if _cache_pool:
        _cache_pool.disconnect()

@contextmanager
def get_cache_conn():
    """Yield a blocking Redis client on the shared pool, or None if not initialised."""
    if not _cache_pool:
        yield None
        return

    conn = Redis(connection_pool=_cache_pool)
    try:
        yield conn
    finally:
        pass