"""Process-wide Postgres connection pool.

The pool is synchronous psycopg (psycopg_pool.ConnectionPool). Code on the async
request path must not use it directly: run the query in a worker thread with
asyncio.to_thread (see stores/search.py). Rows come back as dicts, and pgvector
types are registered on every connection. The schema is managed by the Alembic
migrations in migrations/, not by this module.
"""
import psycopg
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from contextlib import contextmanager
from rag_engine.config import get_settings

_db_pool: ConnectionPool | None = None

def init_db_pool() -> None:
    """Create the pool from settings. Called once at app startup (main.lifespan)."""
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
    """The pool, or None before init_db_pool (or if it failed)."""
    return _db_pool

def close_db_pool() -> None:
    if _db_pool:
        _db_pool.close()

@contextmanager
def get_db_conn():
    """Borrow a pooled connection for a `with` block (blocking).

    The connection commits on normal exit and rolls back on an exception. Raises
    AttributeError if the pool was never initialised, which callers treat as the
    database being unavailable.
    """
    with _db_pool.connection() as conn:
        yield conn