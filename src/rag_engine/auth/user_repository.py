"""Postgres adapter for persistent authentication users."""

import psycopg

from rag_engine.api.errors import AuthUnavailable
from rag_engine.auth.interfaces import User
from rag_engine.auth.tiers import Tier
from rag_engine.stores.db import get_db_conn

_USER_SELECT = """
    SELECT u.uid, u.username, u.password, u.is_active, r.name AS tier
    FROM users AS u
    JOIN role AS r ON r.rid = u.role_rid
"""


def ensure_auth_schema() -> None:
    """Bring an already-initialized database in line with scripts/init_pgvector.sql.

    That script only runs on a fresh Postgres volume, so a database created
    before these columns/rows existed needs them applied here instead. Safe to
    call on every startup.
    """
    with get_db_conn() as conn:
        conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_username_idx ON users (username)")
        for rid, tier in enumerate(Tier, start=1):
            conn.execute(
                "INSERT INTO role (rid, name) VALUES (%s, %s) ON CONFLICT (rid) DO NOTHING",
                (rid, tier.value),
            )


def _to_user(row: dict) -> User:
    password = row["password"]
    if isinstance(password, (bytes, bytearray, memoryview)):
        password_hash = bytes(password).decode("utf-8")
    else:
        password_hash = str(password)
    return User(
        user_id=row["uid"],
        username=row["username"],
        password_hash=password_hash,
        tier=Tier(row["tier"]),
        is_active=bool(row["is_active"]),
    )


class PostgresUserRepository:
    """Datamapper for the existing ``users`` and ``role`` tables."""

    @staticmethod
    def _unavailable(error: Exception) -> AuthUnavailable:
        return AuthUnavailable("Authentication database unavailable")

    async def get_by_id(self, user_id: int) -> User | None:
        try:
            with get_db_conn() as conn:
                row = conn.execute(
                    _USER_SELECT + " WHERE u.uid = %s",
                    (user_id,),
                ).fetchone()
        except (psycopg.Error, AttributeError, RuntimeError) as error:
            raise self._unavailable(error) from error
        return _to_user(row) if row is not None else None

    async def get_by_username(self, username: str) -> User | None:
        try:
            with get_db_conn() as conn:
                row = conn.execute(
                    _USER_SELECT + " WHERE u.username = %s",
                    (username,),
                ).fetchone()
        except (psycopg.Error, AttributeError, RuntimeError) as error:
            raise self._unavailable(error) from error
        return _to_user(row) if row is not None else None

    async def create(self, username: str, password_hash: str, tier: Tier) -> User | None:
        try:
            with get_db_conn() as conn:
                row = conn.execute(
                    """
                    INSERT INTO users (role_rid, username, password)
                    SELECT rid, %s, %s
                    FROM role
                    WHERE name = %s
                    RETURNING uid
                    """,
                    (username, password_hash.encode("utf-8"), tier.value),
                ).fetchone()
                if row is None:
                    raise AuthUnavailable("Authentication role is not configured")
                created = conn.execute(
                    _USER_SELECT + " WHERE u.uid = %s",
                    (row["uid"],),
                ).fetchone()
        except AuthUnavailable:
            raise
        except psycopg.errors.UniqueViolation:
            return None
        except (psycopg.Error, AttributeError, RuntimeError) as error:
            raise self._unavailable(error) from error
        return _to_user(created)

    async def update_password_hash(self, user_id: int, password_hash: str) -> None:
        try:
            with get_db_conn() as conn:
                conn.execute(
                    "UPDATE users SET password = %s WHERE uid = %s",
                    (password_hash.encode("utf-8"), user_id),
                )
        except (psycopg.Error, AttributeError, RuntimeError) as error:
            raise self._unavailable(error) from error

    async def update_tier(self, user_id: int, tier: Tier) -> bool:
        try:
            with get_db_conn() as conn:
                result = conn.execute(
                    """
                    UPDATE users AS u
                    SET role_rid = r.rid
                    FROM role AS r
                    WHERE u.uid = %s AND r.name = %s
                    """,
                    (user_id, tier.value),
                )
                return result.rowcount > 0
        except (psycopg.Error, AttributeError, RuntimeError) as error:
            raise self._unavailable(error) from error

    async def set_active(self, user_id: int, is_active: bool) -> bool:
        try:
            with get_db_conn() as conn:
                result = conn.execute(
                    "UPDATE users SET is_active = %s WHERE uid = %s",
                    (is_active, user_id),
                )
                return result.rowcount > 0
        except (psycopg.Error, AttributeError, RuntimeError) as error:
            raise self._unavailable(error) from error