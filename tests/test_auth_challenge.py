"""WWW-Authenticate challenges on 401 responses (RFC 7235 section 3.1, RFC 6750 section 3)."""
import time

import jwt
import pytest

from rag_engine.api.errors import InvalidCredentials, SessionExpired
from rag_engine.auth.dependencies import get_auth_service
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.config import get_settings

RESOLVE_BODY = {"code": "am.fb.0002"}


def _encode(**overrides) -> str:
    """Sign a token with valid defaults, so each test changes only what it is about."""
    settings = get_settings()
    now = int(time.time())
    claims = {
        "sub": "1",
        "tier": Tier.technician.value,
        "typ": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + 900,
    } | overrides
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


class StubAuthService:
    def __init__(self, error):
        self._error = error

    async def refresh(self, refresh_token):
        raise self._error

    async def login(self, username, password, client_ip):
        raise self._error


def test_missing_token_gets_a_bare_challenge(client):
    r = client.post("/api/v1/resolve", json=RESOLVE_BODY)

    assert r.status_code == 401
    # RFC 6750 3.1: with no credentials sent, the challenge names no error.
    assert r.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    ("label", "token"),
    [
        ("malformed", "not-a-jwt"),
        ("expired", _encode(iat=int(time.time()) - 3600, exp=int(time.time()) - 60)),
        ("wrong type", _encode(typ="refresh")),
        ("unknown tier", _encode(tier="not-a-tier")),
        ("wrong audience", _encode(aud="someone-else")),
    ],
)
def test_rejected_token_challenge_names_the_error(client, label, token):
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/v1/resolve", json=RESOLVE_BODY, headers=headers)

    assert r.status_code == 401, label
    challenge = r.headers["www-authenticate"]
    assert challenge.startswith("Bearer "), label
    assert 'error="invalid_token"' in challenge, label
    assert r.json()["error"]["code"] == "unauthorized", label


def test_forbidden_carries_no_challenge(client):
    token, _ = create_access_token(user_id=1, tier=Tier.operator)
    body = {"conversation_id": "c-1", "message": "Why did the drive fault?"}

    r = client.post("/api/v1/chat", json=body, headers={"Authorization": f"Bearer {token}"})

    # A challenge on 403 would invite a pointless retry: the tier, not the token, is the problem.
    assert r.status_code == 403
    assert "www-authenticate" not in r.headers


@pytest.mark.parametrize(
    ("path", "kwargs", "error", "expected_code"),
    [
        ("/auth/refresh", {}, SessionExpired(), "session_expired"),
        ("/auth/token", {"data": {"username": "a", "password": "b"}},
         InvalidCredentials(), "invalid_credentials"),
    ],
)
def test_auth_endpoint_401s_carry_a_challenge(client, path, kwargs, error, expected_code):
    client.app.dependency_overrides[get_auth_service] = lambda: StubAuthService(error)

    r = client.post(path, **kwargs)

    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json()["error"]["code"] == expected_code
