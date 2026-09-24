from redis import ConnectionPool, Redis
from contextlib import contextmanager
from rag_engine.config import get_settings

_cache_pool: ConnectionPool | None = None
_cache_client: Redis | None = None

def init_cache_pool() -> None:
    global _cache_pool, _cache_client
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
    _cache_client = Redis(connection_pool=_cache_pool)

def get_cache_client() -> Redis | None:
    return _cache_client

def close_cache_pool() -> None:
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