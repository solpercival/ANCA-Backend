"""
API router for login, token refresh, logout, and the current account.

Mounted under /auth. Login returns the access token in the response body and
sets the refresh token as an HttpOnly cookie scoped to /auth, so the browser only
sends it to these endpoints. The refresh and logout endpoints authenticate with
that cookie and therefore run the check_origin CSRF guard.

The handlers only translate between HTTP and AuthService; the logic lives there.
"""

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from rag_engine.api.errors import Forbidden
from rag_engine.auth.dependencies import (
    check_origin,
    current_principal,
    current_user,
    get_auth_service,
)
from rag_engine.auth.interfaces import User
from rag_engine.auth.tiers import Principal
from rag_engine.auth.schemas import (
    TokenResponse,
    UserOut,
)
from rag_engine.auth.service import AuthService, TokenPair
from rag_engine.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/auth"


def _token_response(response: Response, pair: TokenPair) -> TokenResponse:
    """Set the refresh cookie from a token pair and return the access token body."""
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        pair.refresh_token,
        max_age=pair.refresh_max_age,
        path=REFRESH_COOKIE_PATH,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )
    return TokenResponse(access_token=pair.access_token, expires_in=pair.expires_in)


def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh cookie. The attributes must match those used when it was set."""
    settings = get_settings()
    response.delete_cookie(
        REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )


@router.post("/token", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Log in with a form-encoded username and password.

    Returns the access token and sets the refresh cookie. Responds 401 for bad
    credentials and 429 when the login rate limit is reached.
    """
    # Behind a reverse proxy, run uvicorn with --proxy-headers so this is the real client.
    client_ip = request.client.host if request.client else "unknown"
    pair = await auth.login(form.username, form.password, client_ip)
    return _token_response(response, pair)


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(check_origin)])
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Exchange the refresh cookie for a new access token and a rotated refresh cookie.

    Responds 401 when the session has expired or been revoked; the client should
    send the user back to login.
    """
    pair = await auth.refresh(refresh_token)
    return _token_response(response, pair)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_origin)],
)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> None:
    """End the current session and clear the refresh cookie. Succeeds even without a cookie."""
    await auth.logout(refresh_token)
    _clear_refresh_cookie(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    principal: Principal = Depends(current_principal),
    auth: AuthService = Depends(get_auth_service),
) -> None:
    """
    End every session for the caller's account and clear the refresh cookie.

    Requires a valid bearer token rather than the cookie.
    """
    await auth.logout_all(int(principal.subject))
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> UserOut:
    """Return the caller's account, read from the database rather than the token."""
    return UserOut.model_validate(user)
