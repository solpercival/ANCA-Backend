"""
Access and refresh token primitives.

Access tokens are short-lived JWTs signed with the shared secret. They carry the
user ID and tier, so a request can be authorised without a storage lookup.

Refresh tokens are opaque random strings. The server stores only their SHA-256
digest, so a leak of the session store does not expose usable tokens.
"""

import hashlib
import secrets
import time

import jwt

from rag_engine.api.errors import Unauthorized
from rag_engine.auth.tiers import Principal, Tier
from rag_engine.config import get_settings

ACCESS_TOKEN_TYPE = "access"


def create_access_token(user_id: int, tier: Tier) -> tuple[str, int]:
    """
    Create a signed access token for a user.

    The token includes the issuer, audience and expiry from settings, plus a
    random `jti` so every token is unique.

    Returns:
        `(token, lifetime_seconds)`.
    """
    settings = get_settings()
    now = int(time.time())
    ttl = settings.access_token_ttl_minutes * 60
    claims = {
        "sub": str(user_id),
        "tier": tier.value,
        "typ": ACCESS_TOKEN_TYPE,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + ttl,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm), ttl


def decode_access_token(token: str) -> Principal:
    """
    Verify an access token and return the caller it identifies.

    Checks the signature, algorithm, expiry, issuer, audience and required claims,
    then confirms the token type and tier are ones this service issues.

    Raises:
        Unauthorized: The token is malformed, expired, wrongly signed, not an
            access token, or names an unknown tier.
    """
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["sub", "tier", "typ", "iat", "exp"]},
        )
    except jwt.InvalidTokenError as exc:
        raise Unauthorized("Invalid or expired token") from exc
    if claims["typ"] != ACCESS_TOKEN_TYPE:
        raise Unauthorized("Invalid token type")
    try:
        tier = Tier(claims["tier"])
    except ValueError as exc:
        raise Unauthorized("Invalid token tier") from exc
    return Principal(subject=claims["sub"], tier=tier)


def new_refresh_token() -> str:
    """Generate a new opaque refresh token with 256 bits of randomness."""
    return secrets.token_urlsafe(32)


def digest(refresh_token: str) -> str:
    """Return the hex SHA-256 digest used as a refresh token's storage key.

    Refresh tokens carry 256 random bits, so a fast unsalted hash is sufficient.
    """
    return hashlib.sha256(refresh_token.encode()).hexdigest()
