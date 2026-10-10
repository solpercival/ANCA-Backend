"""Shared async client for the API contract tests.

Requests go straight to the FastAPI app in this process.
App startup is skipped, so the tests do not connect to Postgres, Redis, or Ollama.
The stand-in orchestrator always includes likely causes
While each route applies the caller's tier and will show/hide likely causes accordingly.
Redis and the rate-limit backend are left unset, so requests are not rate limited.
"""
import httpx
import pytest

from rag_engine.api.errors import ModelUnavailable, RetrievalUnavailable, UnknownAlarmCode
from rag_engine.api.schemas import ChatResponse, ResolveResponse
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.main import app
from rag_engine.orchestrator import get_orchestrator

RESOLVE_BODY = {"code": "am.fb.0002"}
CHAT_BODY = {"conversation_id": "c-1", "message": "Why did the drive fault?"}
REQUEST_ID = "req-contract"

# Attributes contract tests may replace. Teardown puts the shared app back so
# the sync TestClient fixtures do not see leftovers from this suite.
_RESTORED_STATE = ("pg_pool", "redis", "rate_limit_backend")


class StubOrchestrator:
    """Returns likely causes for every tier, so the route's gate is what gets tested."""

    async def resolve(self, req, tier):
        return ResolveResponse(
            code=req.code,
            steps=["Reset the drive."],
            likely_causes=["Loose EtherCAT cable."],
            tier=tier,
        )

    async def chat(self, req, tier):
        return ChatResponse(conversation_id=req.conversation_id, reply="Try step 1.")


def _auth(tier: Tier = Tier.technician) -> dict[str, str]:
    token, _ = create_access_token(user_id=1, tier=tier)
    return {"Authorization": f"Bearer {token}"}


def _snapshot_state() -> dict[str, tuple[bool, object]]:
    saved: dict[str, tuple[bool, object]] = {}
    for name in _RESTORED_STATE:
        if hasattr(app.state, name):
            saved[name] = (True, getattr(app.state, name))
        else:
            saved[name] = (False, None)
    return saved


def _restore_state(saved: dict[str, tuple[bool, object]]) -> None:
    for name, (present, value) in saved.items():
        if present:
            setattr(app.state, name, value)
        elif hasattr(app.state, name):
            delattr(app.state, name)


@pytest.fixture
async def client():
    """Async client against the ASGI app. Does not run the app lifespan."""
    saved = _snapshot_state()
    # No Redis and no stand-in backend: rate_limit_dependency returns immediately.
    for name in ("redis", "rate_limit_backend"):
        if hasattr(app.state, name):
            delattr(app.state, name)
    app.dependency_overrides[get_orchestrator] = lambda: StubOrchestrator()
    try:
        # ASGITransport never runs the lifespan (and has no `lifespan` argument).
        # raise_app_exceptions=False: return the app's 500 response like a real HTTP
        # client would, instead of re-raising the unhandled exception into the test.
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
            yield http
    finally:
        app.dependency_overrides.clear()
        _restore_state(saved)


class _RaisingOrchestrator:
    def __init__(self, exc: Exception):
        self._exc = exc

    async def resolve(self, req, tier):
        raise self._exc


def _headers(tier: Tier = Tier.technician, request_id: str = REQUEST_ID) -> dict[str, str]:
    return {**_auth(tier), "x-request-id": request_id}


def _assert_error(response, *, status: int, code: str, request_id: str = REQUEST_ID) -> dict:
    assert response.status_code == status
    assert response.headers["x-request-id"] == request_id
    error = response.json()["error"]
    assert error["code"] == code
    assert error["message"]
    assert error["request_id"] == request_id
    return error


class _PostgresProbe:
    """connection() is the context manager the readiness route uses."""

    def __init__(self, *, row: object = (1,), error: Exception | None = None):
        self._row = row
        self._error = error

    def connection(self, timeout: float = 0):
        return _PostgresConnection(self._row, self._error)


class _PostgresConnection:
    def __init__(self, row: object, error: Exception | None):
        self._row = row
        self._error = error

    def __enter__(self):
        if self._error is not None:
            raise self._error
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, _sql: str):
        return self

    def fetchone(self):
        return self._row


class _RedisProbe:
    def __init__(self, *, result: bool = True, error: Exception | None = None):
        self._result = result
        self._error = error

    async def ping(self) -> bool:
        if self._error is not None:
            raise self._error
        return self._result


class _ModelResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class _ModelClient:
    def __init__(self, *, status_code: int, error: Exception | None):
        self._status_code = status_code
        self._error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, _url: str):
        if self._error is not None:
            raise self._error
        return _ModelResponse(self._status_code)


def _drop_state(name: str) -> None:
    if hasattr(app.state, name):
        delattr(app.state, name)


def _install_model_client(
    monkeypatch,
    *,
    status_code: int = 200,
    error: Exception | None = None,
) -> None:
    client = _ModelClient(status_code=status_code, error=error)

    def factory(*_args, **_kwargs):
        return client

    monkeypatch.setattr("rag_engine.api.routes.httpx.AsyncClient", factory)


def _configure_probes(monkeypatch, pg: str, redis: str, model: str) -> None:
    if pg == "ok":
        app.state.pg_pool = _PostgresProbe()
    elif pg == "down":
        app.state.pg_pool = _PostgresProbe(error=ConnectionError("postgres down"))
    else:
        _drop_state("pg_pool")

    if redis == "ok":
        app.state.redis = _RedisProbe()
    elif redis == "down":
        app.state.redis = _RedisProbe(result=False)
    else:
        _drop_state("redis")

    if model == "ok":
        _install_model_client(monkeypatch, status_code=200)
    elif model == "down":
        _install_model_client(monkeypatch, status_code=503)
    else:
        _install_model_client(monkeypatch, error=ConnectionError("model down"))


@pytest.mark.parametrize(
    ("exc", "status", "code"),
    [
        (UnknownAlarmCode(), 404, "unknown_alarm_code"),
        (RetrievalUnavailable(), 503, "retrieval_unavailable"),
        (ModelUnavailable(), 503, "model_unavailable"),
    ],
)
async def test_resolve_app_errors_use_the_error_envelope(client, exc, status, code):
    app.dependency_overrides[get_orchestrator] = lambda: _RaisingOrchestrator(exc)

    response = await client.post("/api/v2/resolve", json=RESOLVE_BODY, headers=_headers())

    _assert_error(response, status=status, code=code)


async def test_unhandled_resolve_error_hides_the_exception(client):
    app.dependency_overrides[get_orchestrator] = lambda: _RaisingOrchestrator(Exception("secret"))

    response = await client.post("/api/v2/resolve", json=RESOLVE_BODY, headers=_headers())

    error = _assert_error(response, status=500, code="internal_error")
    assert error["message"] == "Internal server error"
    assert "secret" not in response.text


async def test_invalid_alarm_code_is_a_validation_error(client):
    response = await client.post(
        "/api/v2/resolve",
        json={"code": "not-a-code"},
        headers=_headers(),
    )

    error = _assert_error(response, status=422, code="validation_error")
    assert error["details"]
    assert error["details"][0]["field"] == "code"


async def test_missing_token_challenge_is_bearer(client):
    response = await client.post("/api/v2/resolve", json=RESOLVE_BODY)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.headers["www-authenticate"] == "Bearer"


async def test_malformed_token_challenge_names_invalid_token(client):
    response = await client.post(
        "/api/v2/resolve",
        json=RESOLVE_BODY,
        headers={"Authorization": "Bearer not-a-jwt"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert 'error="invalid_token"' in response.headers["www-authenticate"]


async def test_operator_chat_has_no_authenticate_challenge(client):
    response = await client.post("/api/v2/chat", json=CHAT_BODY, headers=_auth(Tier.operator))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert "www-authenticate" not in response.headers


@pytest.mark.parametrize(
    ("tier", "sees_causes", "chat_available"),
    [
        (Tier.operator, False, False),
        (Tier.technician, True, True),
        (Tier.partner, True, True),
    ],
)
async def test_resolve_applies_tier_rules(client, tier, sees_causes, chat_available):
    response = await client.post("/api/v2/resolve", json=RESOLVE_BODY, headers=_auth(tier))

    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == tier.value
    assert bool(body["likely_causes"]) is sees_causes
    if tier is Tier.operator:
        assert body["likely_causes"] == []
    assert body["ai_chat_available"] is chat_available


@pytest.mark.parametrize(
    ("tier", "status"),
    [(Tier.operator, 403), (Tier.technician, 200), (Tier.partner, 200)],
)
async def test_chat_is_limited_to_tiers_that_can_use_it(client, tier, status):
    response = await client.post("/api/v2/chat", json=CHAT_BODY, headers=_auth(tier))

    assert response.status_code == status
    if status == 403:
        assert response.json()["error"]["code"] == "forbidden"


@pytest.mark.parametrize(
    ("pg", "redis", "model", "status", "checks"),
    [
        ("ok", "ok", "ok", 200, {"postgres": True, "redis": True, "model_server": True}),
        ("down", "ok", "ok", 503, {"postgres": False, "redis": True, "model_server": True}),
        ("ok", "down", "ok", 503, {"postgres": True, "redis": False, "model_server": True}),
        ("ok", "ok", "down", 503, {"postgres": True, "redis": True, "model_server": False}),
        (
            "missing",
            "missing",
            "raise",
            503,
            {"postgres": False, "redis": False, "model_server": False},
        ),
    ],
)
async def test_ready_reports_each_dependency(client, monkeypatch, pg, redis, model, status, checks):
    _configure_probes(monkeypatch, pg, redis, model)

    response = await client.get("/api/v2/ready", headers={"x-request-id": REQUEST_ID})

    assert response.status_code == status
    assert response.headers["x-request-id"] == REQUEST_ID
    body = response.json()
    assert body["status"] == ("ok" if status == 200 else "not_ready")
    assert body["checks"] == checks
