"""Shared async client for the API contract tests.

Requests go straight to the FastAPI app in this process.
App startup is skipped, so the tests do not connect to Postgres, Redis, or Ollama.
The stand-in orchestrator always includes likely causes
While each route applies the caller's tier and will show/hide likely causes accordingly.
Redis and the rate-limit backend are left unset, so requests are not rate limited.
"""
import httpx
import pytest

from rag_engine.api.schemas import ChatResponse, ResolveResponse
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.main import app
from rag_engine.orchestrator import get_orchestrator

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
        transport = httpx.ASGITransport(app=app, lifespan="off")
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
            yield http
    finally:
        app.dependency_overrides.clear()
        _restore_state(saved)
