"""
Storage contracts for authentication.

Postgres backs UserRepository and Redis backs SessionStore. Auth logic depends
only on these protocols; concrete adapters are attached to app.state in the
lifespan (see main.py). Adapters should raise api.errors.AuthUnavailable when
their backend cannot be reached, so the client gets a handled 503.

The SessionStore docstrings give the Redis commands and key layout each method
is expected to use. Every Redis key an adapter writes must carry a TTL.
"""

from dataclasses import dataclass
from typing import Protocol

from rag_engine.auth.tiers import Tier


@dataclass(frozen=True)
class User:
    """
    A stored account.

    Attributes:
        user_id: Primary key; also the access token's `sub` claim.
        username: Normalised (trimmed, lower-case) login name.
        password_hash: Encoded Argon2id hash.
        tier: The account's access level.
        is_active: False once the account is deactivated; inactive users cannot
            log in or refresh.
    """

    user_id: int
    username: str
    password_hash: str
    tier: Tier
    is_active: bool


@dataclass(frozen=True)
class SessionFamily:
    """One login. Every refresh token issued from it shares the family_id.

    Revoking the family ends that login on the device that made it, without
    affecting the user's other sessions.
    """

    family_id: str
    user_id: int
    created_at: int  # unix seconds


@dataclass(frozen=True)
class Rotation:
    """Tombstone left behind when a refresh token is exchanged for a new one.

    Lets a later attempt to spend the same token be recognised as reuse, and
    tells the service which family to revoke.
    """

    family_id: str
    rotated_at: int  # unix seconds


class UserRepository(Protocol):
    """Persistent account storage, implemented against Postgres."""

    async def get_by_id(self, user_id: int) -> User | None:
        """Return the user with this ID, or None if there is none."""
        ...

    async def get_by_username(self, username: str) -> User | None:
        """Return the user with this normalised username, or None if there is none."""
        ...

    async def create(self, username: str, password_hash: str, tier: Tier) -> User | None:
        """Insert a user. Return None if the username is already taken."""
        ...

    async def update_password_hash(self, user_id: int, password_hash: str) -> None:
        """Replace a user's stored password hash."""
        ...

    async def update_tier(self, user_id: int, tier: Tier) -> bool:
        """Change a user's tier. Return False if no such user."""
        ...

    async def set_active(self, user_id: int, is_active: bool) -> bool:
        """Activate or deactivate a user. Return False if no such user."""
        ...


class SessionStore(Protocol):
    """Refresh-token sessions and login rate limits, implemented against Redis."""

    async def put_token(self, digest: str, family_id: str, ttl: int) -> None:
        """Record a live refresh token and the family it belongs to.

        SET auth:rt:{digest} family_id EX ttl
        """
        ...

    async def take_token(self, digest: str) -> str:
        """Consume a refresh token, returning its family_id or None if it is not live.

        GETDEL auth:rt:{digest}. Must be atomic: a token is spendable exactly once.
        """
        ...

    async def mark_rotated(self, digest: str, rotation: Rotation, ttl: int) -> None:
        """Leave a tombstone for a refresh token that has just been exchanged.

        SET auth:rt_used:{digest} rotation EX ttl
        """
        ...

    async def get_rotation(self, digest: str) -> Rotation | None:
        """Return the tombstone for a previously exchanged token, if one remains.

        GET auth:rt_used:{digest}
        """
        ...

    async def save_family(self, family: SessionFamily, ttl: int) -> None:
        """Create or extend a session family and index it under its user.

        SET auth:fam:{family_id} EX ttl, and SADD it to auth:user_fams:{user_id}.
        """
        ...

    async def get_family(self, family_id: str) -> SessionFamily | None:
        """Return a live session family, or None if it expired or was revoked.

        GET auth:fam:{family_id}
        """
        ...

    async def revoke_family(self, family_id: str) -> None:
        """End one login.

        DEL auth:fam:{family_id} and remove it from its user's set.
        """
        ...

    async def revoke_user_sessions(self, user_id: int) -> None:
        """End every login for a user.

        DEL every family in auth:user_fams:{user_id}, then the set itself.
        """
        ...

    async def set_not_before(self, user_id: int, timestamp: int, ttl: int) -> None:
        """Record the time before which a user's access tokens should be rejected.

        SET auth:nbf:{user_id} timestamp EX ttl
        """
        ...

    async def failed_attempts(self, key: str) -> int:
        """Return the failed login count for a rate-limit key.

        GET auth:rl:{key}, 0 if absent.
        """
        ...

    async def record_failed_attempt(self, key: str, window: int) -> None:
        """Count a failed login, starting the window on the first failure.

        INCR auth:rl:{key}, then EXPIRE auth:rl:{key} window NX.
        """
        ...

    async def clear_failed_attempts(self, key: str) -> None:
        """Reset the failed login count for a rate-limit key.

        DEL auth:rl:{key}
        """
        ...
