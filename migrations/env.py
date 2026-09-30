"""Alembic environment: schema migrations for the RAG engine's Postgres database.

The URL comes from the app's own settings (POSTGRES_* env vars / .env), so there
is one source of truth for where the database lives. There is no SQLAlchemy
model layer, so migrations are hand-written (no autogenerate).
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from rag_engine.config import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None  # no ORM models; autogenerate is not used


def _database_url() -> str:
    # postgres_dsn is a libpq URL ("postgresql://..."); SQLAlchemy needs the driver
    # named explicitly to use psycopg 3, which is what the app already installs.
    dsn = get_settings().postgres_dsn
    return dsn.replace("postgresql://", "postgresql+psycopg://", 1)


def run_migrations_offline() -> None:
    """Emit the SQL to stdout instead of connecting (`alembic upgrade head --sql`)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply migrations."""
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
