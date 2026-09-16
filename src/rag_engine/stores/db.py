import psycopg
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from contextlib import contextmanager
from rag_engine.config import get_settings

_pool: ConnectionPool | None = None

def init_pool() -> None:
    settings = get_settings()
    global _pool
    _pool = ConnectionPool(
        settings.postgres_dsn,
        min_size=1,
        max_size=100,
        kwargs={"row_factory": dict_row}
    )

def close_pool() -> None:
    if _pool:
        _pool.close()

@contextmanager
def get_conn():
    with _pool.connection() as conn:
        yield conn