"""Postgres adapter for persistent authentication users."""

import asyncio

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
    """Bring an older database's auth tables in line with migration 0001.

    Databases created before users.is_active / the username index / the role
    seed rows existed need them applied; the same objects are in
    migrations/versions/0001_initial_schema.py. Safe to call on every startup.
    """
    with get_db_conn() as conn:
        conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"
        )
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_username_idx ON users (username)")
        for rid, tier in enumerate(Tier, start=1):
            conn.execute(
                "INSERT INTO role (rid, name) VALUES (%s, %s) ON CONFLICT (rid) DO NOTHING",
                (rid, tier.value),
            )


def _to_user(row: dict) -> User:
    """Build a User from a _USER_SELECT row. The password column is BYTEA holding
    the UTF-8 hash string, so it is decoded back to text here."""
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
    """Datamapper for the existing ``users`` and ``role`` tables.

    The pool is synchronous psycopg, so every async method runs its query in a
    worker thread via a _*_sync helper instead of blocking the event loop. Any
    database failure (including an uninitialised pool) is raised as AuthUnavailable.
    """

    @staticmethod
    def _unavailable(error: Exception) -> AuthUnavailable:
        """The error returned to clients for any database failure; the cause is
        chained by the caller (`raise ... from error`) and never put in the message."""
        return AuthUnavailable("Authentication database unavailable")

    async def get_by_id(self, user_id: int) -> User | None:
        """The user with this id, or None if there is none."""
        return await asyncio.to_thread(self._get_by_id_sync, user_id)

    def _get_by_id_sync(self, user_id: int) -> User | None:
        """Blocking query for get_by_id; runs in a worker thread."""
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
        """The user with this exact username, or None. The match is case-sensitive,
        so pass the normalised username."""
        return await asyncio.to_thread(self._get_by_username_sync, username)

    def _get_by_username_sync(self, username: str) -> User | None:
        """Blocking query for get_by_username; runs in a worker thread."""
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
        """Insert a user and return it, or None if the username is already taken.
        Raises AuthUnavailable if the tier has no row in the role table."""
        return await asyncio.to_thread(self._create_sync, username, password_hash, tier)

    def _create_sync(self, username: str, password_hash: str, tier: Tier) -> User | None:
        """Blocking insert for create; runs in a worker thread. The hash is stored
        as UTF-8 bytes (the password column is BYTEA)."""
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
        """Replace the stored password hash. Does nothing if the user doesn't exist."""
        return await asyncio.to_thread(self._update_password_hash_sync, user_id, password_hash)

    def _update_password_hash_sync(self, user_id: int, password_hash: str) -> None:
        """Blocking update for update_password_hash; runs in a worker thread."""
        try:
            with get_db_conn() as conn:
                conn.execute(
                    "UPDATE users SET password = %s WHERE uid = %s",
                    (password_hash.encode("utf-8"), user_id),
                )
        except (psycopg.Error, AttributeError, RuntimeError) as error:
            raise self._unavailable(error) from error

    async def update_tier(self, user_id: int, tier: Tier) -> bool:
        """Change the user's tier. False if the user or the tier's role row is missing."""
        return await asyncio.to_thread(self._update_tier_sync, user_id, tier)

    def _update_tier_sync(self, user_id: int, tier: Tier) -> bool:
        """Blocking update for update_tier; runs in a worker thread."""
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
        """Enable or disable the account. False if the user doesn't exist."""
        return await asyncio.to_thread(self._set_active_sync, user_id, is_active)

    def _set_active_sync(self, user_id: int, is_active: bool) -> bool:
        """Blocking update for set_active; runs in a worker thread."""
        try:
            with get_db_conn() as conn:
                result = conn.execute(
                    "UPDATE users SET is_active = %s WHERE uid = %s",
                    (is_active, user_id),
                )
                return result.rowcount > 0
        except (psycopg.Error, AttributeError, RuntimeError) as error:
            raise self._unavailable(error) from error
