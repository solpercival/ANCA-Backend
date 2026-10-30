"""Tier rules enforced by the resolve and chat routes."""

import asyncio
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from rag_engine.api.routes import ESCALATION_NOTE
from rag_engine.api.safety import is_safety_alarm
from rag_engine.api.schemas import ChatResponse, ResolveRequest, ResolveResponse
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.config import API_PREFIX, get_settings
from rag_engine.main import app
from rag_engine.orchestrator import Orchestrator, get_orchestrator
from rag_engine.retrieval.interfaces import Alarm, Chunk
from tests.fakes import FakeAlarmStore, FakePreprocessor

CHAT_BODY = {"conversation_id": "c-1", "message": "Why did the drive fault?"}


class StubOrchestrator:
    """Returns likely causes for every tier, so the route's gate is what gets tested.
    Severity and coverage are set per test for the escalation rule."""

    def __init__(self, severity_category="Error", doc_coverage="full"):
        self._severity_category = severity_category
        self._doc_coverage = doc_coverage

    async def resolve(self, req, tier):
        return ResolveResponse(
            code=req.code,
            steps=["Reset the drive."],
            likely_causes=["Loose EtherCAT cable."],
            tier=tier,
            severity_category=self._severity_category,
            doc_coverage=self._doc_coverage,
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
    r = stub_client.post(f"{API_PREFIX}/resolve", json={"code": "am.fb.0002"}, headers=_auth(tier))

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
    app.dependency_overrides[get_orchestrator] = lambda: StubOrchestrator(doc_coverage=coverage)

    r = stub_client.post("/api/v2/resolve", json={"code": "am.fb.0002"}, headers=_auth(tier))

    assert r.status_code == 200
    assert r.json()["escalation_suggested"] is expected


def test_escalation_suggestion_can_be_disabled(stub_client, monkeypatch):
    from rag_engine.api import routes

    monkeypatch.setattr(routes.settings, "escalation_suggestion_enabled", False)
    app.dependency_overrides[get_orchestrator] = lambda: StubOrchestrator(doc_coverage="partial")

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
    r = stub_client.post(f"{API_PREFIX}/chat", json=CHAT_BODY, headers=_auth(tier))

    assert r.status_code == status
    if status == 403:
        assert r.json()["error"]["code"] == "forbidden"


def test_chat_without_token_is_unauthorized(stub_client):
    r = stub_client.post(f"{API_PREFIX}/chat", json=CHAT_BODY)

    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


# --- operator escalation (tier rule, applied by the route) -------------------


def _resolve_as(tier, orchestrator):
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    try:
        r = TestClient(app).post(
            f"{API_PREFIX}/resolve", json={"code": "am.cfg.0001"}, headers=_auth(tier)
        )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200
    return r.json()


@pytest.mark.parametrize(
    ("severity", "coverage", "operator_escalates"),
    [
        ("Fatal", "full", True),  # safety alarm, even when fully documented
        ("Fatal", "partial", True),
        ("Fatal", "none", True),
        ("Error", "partial", True),  # not safety, but no complete documented fix
        ("Error", "none", True),
        ("Error", "full", False),
        ("Warning", "full", False),
        ("fatal", "full", True),  # category match is case-insensitive
        (None, "full", False),  # alarm without a category
    ],
)
@pytest.mark.parametrize("tier", list(Tier))
def test_escalation_is_suggested_to_operators_only(tier, severity, coverage, operator_escalates):
    body = _resolve_as(tier, StubOrchestrator(severity, coverage))
    expected = operator_escalates and tier is Tier.operator

    assert body["escalation_suggested"] is expected
    assert (body["escalation_note"] == ESCALATION_NOTE) is expected
    if not expected:
        assert body["escalation_note"] is None
    # the nudge never goes into the doc-grounded steps
    assert body["steps"] == ["Reset the drive."]


def test_route_decides_escalation_itself_not_from_the_orchestrators_output():
    class OverclaimingOrchestrator(StubOrchestrator):
        async def resolve(self, req, tier):
            resp = await super().resolve(req, tier)
            resp.escalation_suggested = True
            resp.escalation_note = "made up"
            return resp

    body = _resolve_as(Tier.technician, OverclaimingOrchestrator("Fatal", "none"))

    assert body["escalation_suggested"] is False
    assert body["escalation_note"] is None


def test_safety_set_is_configurable(monkeypatch):
    monkeypatch.setattr(get_settings(), "safety_severity_categories", {"Fatal", "Error"})

    assert is_safety_alarm("Error")
    assert _resolve_as(Tier.operator, StubOrchestrator("Error", "full"))["escalation_suggested"]


# --- safety note (content, set by the orchestrator for every tier) -----------

CFG_0001 = Alarm(
    code="am.cfg.0001",
    title="Logical device mapped multiple times",
    domain="Configuration",
    severity_score=1000,
    severity_category="fatal",  # as stored in the catalogue; rendered "Fatal"
    alarm_text="Startup halted: logical device 5 is mapped to more than one joint.",
    data_fields={},
)


class _Retriever:
    async def retrieve(self, query, top_k, where=None):
        return [Chunk(chunk_id="c1", text="Set the joint logical device.", source="axes.md")]


class _Reranker:
    async def rerank(self, query, chunks, effort):
        return chunks[: effort.reranker_n]


class _Generator:
    def __init__(self, answer):
        self._answer = answer

    async def generate(self, prompt, tokens=None, thinking=False, deterministic=False):
        return self._answer


def _orchestrator(alarm, answer="COVERAGE: full\nSet the joint logical device."):
    return Orchestrator(
        FakePreprocessor(), _Retriever(), _Reranker(), _Generator(answer), FakeAlarmStore(alarm)
    )


@pytest.mark.parametrize("tier", list(Tier))
def test_fatal_alarm_carries_the_safety_note_for_every_tier(tier):
    body = _resolve_as(tier, _orchestrator(CFG_0001))

    assert body["severity_category"] == "Fatal"
    assert body["safety_note"] == "Verify the machine's actual state before acting on these steps."
    assert body["safety_note"] not in body["steps"]
    # fully documented, so only the alarm's severity makes the operator escalate
    assert body["escalation_suggested"] is (tier is Tier.operator)


@pytest.mark.parametrize("tier", list(Tier))
def test_non_fatal_alarm_has_no_safety_note(tier):
    body = _resolve_as(tier, _orchestrator(replace(CFG_0001, severity_category="error")))

    assert body["safety_note"] is None
    assert body["escalation_suggested"] is False


def test_fatal_alarm_keeps_the_safety_note_when_the_docs_do_not_cover_it():
    body = _resolve_as(Tier.operator, _orchestrator(CFG_0001, answer="COVERAGE: none\n"))

    assert body["doc_coverage"] == "none"
    assert body["safety_note"] is not None
    assert body["escalation_suggested"] is True


def test_orchestrator_safety_note_follows_the_configured_set(monkeypatch):
    monkeypatch.setattr(get_settings(), "safety_severity_categories", {"Error"})
    orch = _orchestrator(replace(CFG_0001, severity_category="error"))

    resp = asyncio.run(orch.resolve(ResolveRequest(code="am.cfg.0001"), Tier.technician))

    assert resp.safety_note is not None
