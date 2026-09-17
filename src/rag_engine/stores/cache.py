from redis import ConnectionPool, Redis
from contextlib import contextmanager
from rag_engine.config import get_settings

_cache_pool: ConnectionPool | None = None

def init_cache_pool() -> None:
    settings = get_settings()
    global _cache_pool
    _cache_pool = ConnectionPool(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
        max_connections=100,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )

def close_cache_pool() -> None:
    if _cache_pool:
        _cache_pool.disconnect()

@contextmanager
def get_cache_conn():
    if not _cache_pool:
        return None

    conn = Redis(connection_pool=_cache_pool)
    try:
        yield conn
    finally:
        pass