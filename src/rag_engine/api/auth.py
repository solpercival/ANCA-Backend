"""OAuth2 bearer auth with tier scoping (operator / technician / partner).

The tier travels in the JWT and decides how much detail a resolve response
returns. This module is pure-Python and needs no models, so it runs in CI.
"""
from enum import StrEnum

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from rag_engine.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


class Tier(StrEnum):
    operator = "operator"
    technician = "technician"
    partner = "partner"


class Principal:
    def __init__(self, subject: str, tier: Tier):
        self.subject = subject
        self.tier = tier


def decode_token(token: str) -> Principal:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - exercised in integration
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc
    subject = payload.get("sub")
    tier = payload.get("tier")
    if subject is None or tier not in Tier._value2member_map_:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "malformed token")
    return Principal(subject=subject, tier=Tier(tier))


async def current_principal(token: str | None = Depends(oauth2_scheme)) -> Principal:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    return decode_token(token)
