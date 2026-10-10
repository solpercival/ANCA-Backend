"""Tier rules enforced by the resolve and chat routes."""
import pytest
from fastapi.testclient import TestClient

from rag_engine.api.schemas import ChatResponse, ResolveResponse
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.main import app
from rag_engine.orchestrator import get_orchestrator

CHAT_BODY = {"conversation_id": "c-1", "message": "Why did the drive fault?"}


class StubOrchestrator:
    """Returns likely causes for every tier, so the route's gate is what gets tested."""

    def __init__(self, coverage="full"):
        self.coverage = coverage

    async def resolve(self, req, tier):
        return ResolveResponse(
            code=req.code,
            steps=["Reset the drive."],
            doc_coverage=self.coverage,
            likely_causes=["Loose EtherCAT cable."],
            tier=tier,
        )

    async def chat(self, req, tier):
        return ChatResponse(conversation_id=req.conversation_id, reply="Try step 1.")


@pytest.fixture
def stub_client():
    app.dependency_overrides[get_orchestrator] = lambda: StubOrchestrator()
    yield TestClient(app)
    app.dependency_overrides.clear()


def _auth(tier: Tier) -> dict[str, str]:
    token, _ = create_access_token(user_id=1, tier=tier)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("tier", "sees_causes", "chat_available"),
    [(Tier.operator, False, False), (Tier.technician, True, True), (Tier.partner, True, True)],
)
def test_resolve_applies_tier_rules(stub_client, tier, sees_causes, chat_available):
    r = stub_client.post("/api/v2/resolve", json={"code": "am.fb.0002"}, headers=_auth(tier))

    assert r.status_code == 200
    body = r.json()
    assert body["tier"] == tier.value
    assert bool(body["likely_causes"]) is sees_causes
    assert body["ai_chat_available"] is chat_available


@pytest.mark.parametrize(
    ("tier", "coverage", "expected"),
    [
        (tier, coverage, tier is Tier.operator and coverage != "full")
        for tier in Tier
        for coverage in ("full", "partial", "none")
    ],
)
def test_resolve_escalation_suggestion_matrix(stub_client, tier, coverage, expected):
    app.dependency_overrides[get_orchestrator] = lambda: StubOrchestrator(coverage)

    r = stub_client.post("/api/v2/resolve", json={"code": "am.fb.0002"}, headers=_auth(tier))

    assert r.status_code == 200
    assert r.json()["escalation_suggested"] is expected


def test_escalation_suggestion_can_be_disabled(stub_client, monkeypatch):
    from rag_engine.api import routes

    monkeypatch.setattr(routes.settings, "escalation_suggestion_enabled", False)
    app.dependency_overrides[get_orchestrator] = lambda: StubOrchestrator("partial")

    r = stub_client.post(
        "/api/v2/resolve", json={"code": "am.fb.0002"}, headers=_auth(Tier.operator)
    )

    assert r.status_code == 200
    assert r.json()["escalation_suggested"] is False


@pytest.mark.parametrize(
    ("tier", "status"),
    [(Tier.operator, 403), (Tier.technician, 200), (Tier.partner, 200)],
)
def test_chat_is_limited_to_tiers_that_can_use_it(stub_client, tier, status):
    r = stub_client.post("/api/v2/chat", json=CHAT_BODY, headers=_auth(tier))

    assert r.status_code == status
    if status == 403:
        assert r.json()["error"]["code"] == "forbidden"


def test_chat_without_token_is_unauthorized(stub_client):
    r = stub_client.post("/api/v2/chat", json=CHAT_BODY)

    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"
