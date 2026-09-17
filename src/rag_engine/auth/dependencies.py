"""
FastAPI dependencies for authentication.

Identifies the caller from the bearer token, gates routes by tier, builds
AuthService from the storage adapters on app.state, and guards the
cookie-authenticated endpoints against cross-site requests.

Routes can be protected in three ways:
- `Depends(current_principal)` verifies the token and returns the caller's
  Principal, which is built from the token claims alone and does not hit storage.
- `Depends(require(capability))` verifies the token and checks the caller's tier
  against a capability function in tiers.py, raising Forbidden if the tier is not
  allowed. This is the most common way to protect a route.
- `Depends(current_user)` verifies the token and loads the caller's account record
  from the UserRepository, confirming it still exists and is active. This is only
  needed when the live account record is required, since it hits the database.
"""

from collections.abc import Awaitable, Callable

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from rag_engine.api.errors import AuthUnavailable, Forbidden, Unauthorized
from rag_engine.auth.interfaces import SessionStore, User, UserRepository
from rag_engine.auth.tiers import Principal, Tier
from rag_engine.auth.service import AuthService
from rag_engine.auth.tokens import decode_access_token
from rag_engine.config import get_settings

# auto_error=False so a missing token raises our Unauthorized error body, not FastAPI's.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


async def current_principal(token: str = Depends(oauth2_scheme)) -> Principal:
    """
    Verify the bearer token and return the caller. No database or Redis access.

    Raises:
        Unauthorized: The Authorization header is missing or the token is invalid.
    """
    if not token:
        raise Unauthorized("Missing bearer token")
    return decode_access_token(token)


def require(capability: Callable[[Tier], bool]) -> Callable[..., Awaitable[Principal]]:
    """
    Build a dependency that admits only callers whose tier passes `capability`.

    `capability` is one of the rule functions in tiers.py, so each rule is defined
    once and routes never list tiers inline. Pass the function itself, not a call
    to it: `require(can_use_chat)`, not `require(can_use_chat(...))`.

    Usage: `principal: Principal = Depends(require(can_use_chat))`.
    The resulting dependency raises Unauthorized for a missing or invalid token
    and Forbidden when the caller's tier fails the check.
    """

    async def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if not capability(principal.tier):
            raise Forbidden()
        return principal

    return dependency


def get_user_repository(request: Request) -> UserRepository:
    """
    Return the UserRepository adapter attached to app.state.

    Raises:
        AuthUnavailable: No adapter has been attached.
    """
    users = getattr(request.app.state, "user_repository", None)
    if users is None:
        raise AuthUnavailable("User store is not configured")
    return users


def get_session_store(request: Request) -> SessionStore:
    """
    Return the SessionStore adapter attached to app.state.

    Raises:
        AuthUnavailable: No adapter has been attached.
    """
    sessions = getattr(request.app.state, "session_store", None)
    if sessions is None:
        raise AuthUnavailable("Session store is not configured")
    return sessions


def get_auth_service(
    users: UserRepository = Depends(get_user_repository),
    sessions: SessionStore = Depends(get_session_store),
) -> AuthService:
    """
    Build an AuthService for the current request from the attached adapters.
    """
    return AuthService(users, sessions, get_settings())


async def current_user(
    principal: Principal = Depends(current_principal),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Load the caller's account record, confirming it still exists and is active.

    Unlike current_principal, this hits the database, so the tier and active
    flag are current rather than whatever the token was issued with.

    Raises:
        Unauthorized: The token is invalid, or the account is gone or inactive.
        AuthUnavailable: No user repository is attached.
    """
    user = await users.get_by_id(int(principal.subject))
    if user is None or not user.is_active:
        raise Unauthorized("Account is not active")
    return user


def check_origin(request: Request) -> None:
    """
    CSRF guard for the cookie-authenticated endpoints.

    Browsers always send Origin on cross-site POSTs; a missing header means a
    non-browser client, which cannot be tricked into sending the cookie.

    Raises:
        Forbidden: The Origin header is present but not in `cors_allow_origins`.
    """
    origin = request.headers.get("origin")
    if origin is not None and origin not in get_settings().cors_allow_origins:
        raise Forbidden("Origin not allowed")
