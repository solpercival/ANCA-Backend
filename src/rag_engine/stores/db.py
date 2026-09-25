import psycopg
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from contextlib import contextmanager
from rag_engine.config import get_settings

_db_pool: ConnectionPool | None = None

def init_db_pool() -> None:
    settings = get_settings()
    global _db_pool
    _db_pool = ConnectionPool(
        settings.postgres_dsn,
        min_size=1,
        max_size=100,
        kwargs={"row_factory": dict_row},
        # so a Python list of floats binds as `vector`, not `double precision[]`
        configure=register_vector,
    )

def get_db_pool() -> ConnectionPool | None:
    return _db_pool

def close_db_pool() -> None:
    if _db_pool:
        _db_pool.close()

@contextmanager
def get_db_conn():
    with _db_pool.connection() as conn:
        yield conn