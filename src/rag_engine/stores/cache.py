from redis import ConnectionPool, Redis
from redis.asyncio import Redis as AsyncRedis
from contextlib import contextmanager
from rag_engine.config import get_settings

# sync pool for the blocking callers (session store, search cache);
# async client for request-path callers (rate limiter, health check)
_cache_pool: ConnectionPool | None = None
_async_client: AsyncRedis | None = None

def init_cache_pool() -> None:
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
    return _async_client

async def close_cache_pool() -> None:
    global _async_client
    if _async_client:
        await _async_client.aclose()
        _async_client = None
    if _cache_pool:
        _cache_pool.disconnect()

@contextmanager
def get_cache_conn():
    if not _cache_pool:
        yield None
        return

    conn = Redis(connection_pool=_cache_pool)
    try:
        yield conn
    finally:
        pass