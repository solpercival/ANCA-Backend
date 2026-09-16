"""
Authentication use cases: login, refresh, logout, and account changes.

Knows nothing about HTTP or about which database sits behind the storage
protocols. Raises AppError subclasses so the API layer can render them.

Session model: each login starts a session family. Every refresh consumes the
presented refresh token and issues a new one in the same family. A family lives
for at most `session_max_days` and expires sooner if it goes unused for
`refresh_token_idle_days`. Presenting a refresh token that was already exchanged
is treated as theft and revokes its family, except within a short grace window
that covers concurrent refreshes from the same client.
"""

import secrets
import time
from dataclasses import dataclass
from typing import NoReturn

from rag_engine.api.errors import (
    Conflict,
    InvalidCredentials,
    RateLimited,
    SessionExpired,
    Unauthorized,
)
from rag_engine.auth import passwords, tokens
from rag_engine.auth.interfaces import (
    Rotation,
    SessionFamily,
    SessionStore,
    User,
    UserRepository,
)
from rag_engine.auth.tiers import Tier
from rag_engine.config import Settings

# Two tabs refreshing at the same moment present the same token; that is not theft.
REUSE_GRACE_SECONDS = 20


@dataclass(frozen=True)
class TokenPair:
    """
    Tokens issued by a successful login or refresh.

    Attributes:
        access_token: Signed JWT for the Authorization header.
        expires_in: Access token lifetime in seconds.
        refresh_token: Opaque token for the refresh cookie.
        refresh_max_age: Seconds until the refresh token expires; use as the
            cookie's max-age.
    """

    access_token: str
    expires_in: int
    refresh_token: str
    refresh_max_age: int


def normalize_username(username: str) -> str:
    """Trim surrounding whitespace and lower-case a username so lookups are case-insensitive."""
    return username.strip().lower()


class AuthService:
    """
    Runs authentication use cases against the user and session stores.
    API layer builds one per request.
    """

    def __init__(self, users: UserRepository, sessions: SessionStore, settings: Settings):
        self._users = users
        self._sessions = sessions
        self._settings = settings
        self._refresh_idle = settings.refresh_token_idle_days * 86400
        self._session_max = settings.session_max_days * 86400

    async def create_user(self, username: str, password: str, tier: Tier = Tier.operator) -> User:
        """
        Create an account with a hashed password.

        Raises:
            Conflict: The username, after normalisation, is already taken.
        """
        password_hash = await passwords.hash_password(password)
        user = await self._users.create(normalize_username(username), password_hash, tier)
        if user is None:
            raise Conflict("Username already taken")
        return user

    async def login(self, username: str, password: str, client_ip: str) -> TokenPair:
        """
        Check credentials and start a new session.

        Failed attempts are counted per username and per client IP. A success
        clears the username counter only, so one IP cannot reset its own limit
        by logging into an account it controls. A stale password hash is
        rehashed on success.

        Raises:
            RateLimited: Either counter has reached its limit for the current window.
            InvalidCredentials: The user does not exist, the password is wrong, or
                the account is inactive. The cases are not distinguished.
        """
        username = normalize_username(username)
        limits = {
            f"user:{username}": self._settings.login_max_attempts,
            f"ip:{client_ip}": self._settings.login_max_attempts_per_ip,
        }
        for key, limit in limits.items():
            if await self._sessions.failed_attempts(key) >= limit:
                raise RateLimited(retry_after=self._settings.login_window_seconds)

        user = await self._users.get_by_username(username)
        valid, upgraded_hash = await passwords.verify_password(
            password, user.password_hash if user else None
        )
        if user is None or not valid or not user.is_active:
            for key in limits:
                await self._sessions.record_failed_attempt(key, self._settings.login_window_seconds)
            raise InvalidCredentials()

        await self._sessions.clear_failed_attempts(f"user:{username}")
        if upgraded_hash is not None:
            await self._users.update_password_hash(user.user_id, upgraded_hash)
        family = SessionFamily(
            family_id=secrets.token_urlsafe(16),
            user_id=user.user_id,
            created_at=int(time.time()),
        )
        return await self._issue(user, family)

    async def refresh(self, refresh_token: str | None) -> TokenPair:
        """
        Exchange a refresh token for a new token pair in the same session.

        The presented token is consumed. The user is reloaded, so tier changes
        and deactivation take effect at the next refresh.

        Raises:
            SessionExpired: No token was sent, the token or its session has
                expired or been revoked, the user is gone or inactive, or the
                token was reused outside the grace window (which also revokes
                the session).
            Unauthorized: The token was exchanged by a concurrent request within
                the grace window; the client should retry with the new cookie.
        """
        if not refresh_token:
            raise SessionExpired()
        token_digest = tokens.digest(refresh_token)
        family_id = await self._sessions.take_token(token_digest)
        if family_id is None:
            await self._reject_spent_token(token_digest)

        family = await self._sessions.get_family(family_id)
        if family is None:
            raise SessionExpired()
        # Reload the user so tier changes and deactivation apply at the next refresh.
        user = await self._users.get_by_id(family.user_id)
        if user is None or not user.is_active:
            await self._sessions.revoke_family(family.family_id)
            raise SessionExpired()

        rotation = Rotation(family_id=family.family_id, rotated_at=int(time.time()))
        await self._sessions.mark_rotated(token_digest, rotation, self._refresh_idle)
        return await self._issue(user, family)

    async def logout(self, refresh_token: str | None) -> None:
        """
        End the session the refresh token belongs to.

        Does nothing if the token is missing or no longer live. Access tokens
        already issued stay valid until they expire.
        """
        if not refresh_token:
            return
        family_id = await self._sessions.take_token(tokens.digest(refresh_token))
        if family_id is not None:
            await self._sessions.revoke_family(family_id)

    async def logout_all(self, user_id: int) -> None:
        """End every session for a user and record a not-before time for their access tokens."""
        await self._sessions.revoke_user_sessions(user_id)
        # Recorded now so current_principal can start rejecting older access tokens later.
        access_ttl = self._settings.access_token_ttl_minutes * 60
        await self._sessions.set_not_before(user_id, int(time.time()), access_ttl)

    async def set_tier(self, user_id: int, tier: Tier) -> bool:
        """
        Change a user's tier and end their sessions so the new tier applies on next login.

        Returns:
            False if no such user.
        """
        if not await self._users.update_tier(user_id, tier):
            return False
        await self.logout_all(user_id)
        return True

    async def deactivate(self, user_id: int) -> bool:
        """
        Deactivate a user and end all of their sessions.

        Returns:
            False if no such user.
        """
        if not await self._users.set_active(user_id, False):
            return False
        await self.logout_all(user_id)
        return True

    async def _issue(self, user: User, family: SessionFamily) -> TokenPair:
        """
        Issue a new access token and refresh token for a session family.

        The refresh TTL is the idle timeout, capped by the time left before the
        family reaches its maximum age.

        Raises:
            SessionExpired: The family has reached its maximum age.
        """
        ttl = min(self._refresh_idle, family.created_at + self._session_max - int(time.time()))
        if ttl <= 0:
            raise SessionExpired()
        refresh_token = tokens.new_refresh_token()
        await self._sessions.save_family(family, ttl)
        await self._sessions.put_token(tokens.digest(refresh_token), family.family_id, ttl)
        access_token, expires_in = tokens.create_access_token(user.user_id, user.tier)
        return TokenPair(access_token, expires_in, refresh_token, refresh_max_age=ttl)

    async def _reject_spent_token(self, token_digest: str) -> NoReturn:
        """
        Reject a refresh token that is not live, revoking its family if it was reused.

        Raises:
            Unauthorized: The token was exchanged within the grace window.
            SessionExpired: In every other case.
        """
        rotation = await self._sessions.get_rotation(token_digest)
        if rotation is not None:
            if time.time() - rotation.rotated_at <= REUSE_GRACE_SECONDS:
                raise Unauthorized("Session was refreshed by another request; retry")
            # Reused well after rotation: the token was probably copied, so end that login.
            await self._sessions.revoke_family(rotation.family_id)
        raise SessionExpired()
