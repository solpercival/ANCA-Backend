"""Trusted-host validation, security response headers, and gzip compression."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from rag_engine.api.security import API_CSP, SECURITY_HEADERS, add_security_middleware
from rag_engine.config import Settings
from rag_engine.main import app as main_app

LONG_SECRET = "x" * 40


def _hardened_app(**settings_overrides) -> FastAPI:
    """A minimal app wearing the same middleware stack as the real one."""
    settings = Settings(app_env="local", **settings_overrides)
    app = FastAPI()

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"ok": "yes"}

    @app.get("/big")
    async def big() -> dict[str, str]:
        return {"padding": "compress me " * 200}

    add_security_middleware(app, settings)
    return app


@pytest.mark.parametrize("header", sorted(SECURITY_HEADERS))
def test_security_headers_are_on_successful_responses(client, header):
    r = client.get("/health")

    assert r.headers[header] == SECURITY_HEADERS[header]


@pytest.mark.parametrize("header", sorted(SECURITY_HEADERS))
def test_security_headers_are_on_error_responses(client, header):
    # An error response is still a response an attacker can reach.
    r = client.post("/api/v1/resolve", json={"code": "am.fb.0002"})

    assert r.status_code == 401
    assert r.headers[header] == SECURITY_HEADERS[header]


def test_api_responses_carry_a_restrictive_csp(client):
    r = client.get("/health")

    assert r.headers["content-security-policy"] == API_CSP


@pytest.mark.parametrize("path", ["/docs", "/openapi.json"])
def test_docs_are_exempt_from_the_api_csp(client, path):
    # Swagger loads scripts from a CDN; the API policy would leave a blank page.
    r = client.get(path)

    assert r.status_code == 200
    assert "content-security-policy" not in r.headers


def test_hsts_is_only_sent_over_https():
    # Deliberately not used as a context manager: entering one runs the app lifespan,
    # which waits on Postgres, Redis and Ollama.
    insecure = TestClient(main_app)
    secure = TestClient(main_app, base_url="https://testserver")

    assert "strict-transport-security" not in insecure.get("/health").headers
    assert secure.get("/health").headers["strict-transport-security"].startswith("max-age=")


def test_large_responses_are_compressed():
    with TestClient(_hardened_app()) as client:
        r = client.get("/big", headers={"accept-encoding": "gzip"})

    assert r.headers["content-encoding"] == "gzip"


def test_small_responses_are_not_compressed():
    with TestClient(_hardened_app()) as client:
        r = client.get("/ping", headers={"accept-encoding": "gzip"})

    assert "content-encoding" not in r.headers


def test_requests_for_an_unknown_host_are_rejected():
    app = _hardened_app(allowed_hosts=["api.example.com"])

    with TestClient(app, base_url="http://api.example.com") as allowed:
        assert allowed.get("/ping").status_code == 200

    with TestClient(app, base_url="http://evil.test") as rejected:
        assert rejected.get("/ping").status_code == 400


def test_host_check_ignores_the_port():
    app = _hardened_app(allowed_hosts=["api.example.com"])

    with TestClient(app, base_url="http://api.example.com:8080") as client:
        assert client.get("/ping").status_code == 200


def test_wildcard_hosts_are_rejected_outside_local():
    with pytest.raises(ValidationError, match="ALLOWED_HOSTS"):
        Settings(app_env="production", allowed_hosts=["*"], jwt_secret=LONG_SECRET)


def test_named_hosts_are_accepted_outside_local():
    settings = Settings(
        app_env="production", allowed_hosts=["api.anca.test", "localhost"], jwt_secret=LONG_SECRET
    )

    assert settings.allowed_hosts == ["api.anca.test", "localhost"]
