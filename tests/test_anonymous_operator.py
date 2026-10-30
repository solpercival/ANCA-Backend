"""ALLOW_ANONYMOUS_OPERATOR: /resolve with no bearer token answers as an operator,
while a token that is sent must still be valid and /chat still needs a login."""

import time

import jwt
import pytest

from rag_engine.auth.tiers import Tier
from rag_engine.config import API_PREFIX, get_settings

RESOLVE_BODY = {"code": "am.fb.0002"}


@pytest.fixture
def anonymous_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "allow_anonymous_operator", True)


def _expired_token() -> str:
    settings = get_settings()
    now = int(time.time())
    claims = {
        "sub": "1",
        "tier": Tier.technician.value,
        "typ": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now - 3600,
        "exp": now - 60,
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def test_no_token_is_an_operator_with_the_flag_on(client, anonymous_on):
    r = client.post(f"{API_PREFIX}/resolve", json=RESOLVE_BODY)

    assert r.status_code == 200
    assert r.json()["tier"] == "operator"


def test_no_token_is_unauthorized_with_the_flag_off(client):
    r = client.post(f"{API_PREFIX}/resolve", json=RESOLVE_BODY)

    assert r.status_code == 401


@pytest.mark.parametrize("token", ["not-a-jwt", _expired_token()], ids=["garbage", "expired"])
def test_a_bad_token_is_never_downgraded_to_operator(client, anonymous_on, token):
    r = client.post(
        f"{API_PREFIX}/resolve", json=RESOLVE_BODY, headers={"Authorization": f"Bearer {token}"}
    )

    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_anonymous_caller_gets_the_operator_view(client, anonymous_on):
    body = client.post(f"{API_PREFIX}/resolve", json=RESOLVE_BODY).json()

    assert body["likely_causes"] == []
    assert body["ai_chat_available"] is False
    # am.fb.0002 is only partly covered by the fake docs, so an operator is told to escalate
    assert body["escalation_suggested"] is True
    assert body["escalation_note"]


def test_anonymous_chat_is_unauthorized(client, anonymous_on):
    r = client.post(
        f"{API_PREFIX}/chat", json={"conversation_id": "c1", "message": "How do I reset it?"}
    )

    assert r.status_code == 401


def test_anonymous_calls_share_the_per_ip_limit(client, anonymous_on, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "resolve_rate_limit_per_ip", 1)
    monkeypatch.setattr(settings, "resolve_rate_limit_per_tier", 100)

    first = client.post(f"{API_PREFIX}/resolve", json=RESOLVE_BODY)
    second = client.post(f"{API_PREFIX}/resolve", json=RESOLVE_BODY)

    assert first.status_code == 200
    assert second.status_code == 429
    assert int(second.headers["retry-after"]) > 0
