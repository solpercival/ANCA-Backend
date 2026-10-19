"""Shared pytest fixtures: an app client wired to a fake orchestrator (fake
embedders, stores, reranker and generator), plus a bearer-token header.
Nothing here needs Postgres, Redis or a model server.
"""

import pytest
from fastapi.testclient import TestClient

from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.config import get_settings
from rag_engine.main import app
from rag_engine.orchestrator import Orchestrator, get_orchestrator
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.interfaces import Chunk
from tests.fakes import FakeAlarmStore


class FakeRateLimitBackend:
    def __init__(self):
        self.counts = {}

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        count, ttl = self.counts.get(key, (0, window_seconds))
        count += 1
        self.counts[key] = count, ttl
        return count, ttl


class FakeDenseEmbedder:
    async def dense_embed(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeSparseEmbedder:
    async def sparse_embed(self, texts):
        return [{2: 0.12, 93: 0.4367, 254: 0.111} for _ in texts]


class FakeVectorStore:
    async def semantic_search(self, vector, top_k, where=None):
        return [
            Chunk(
                chunk_id="v1",
                text="Reset the drive. A loose EtherCAT cable causes the drive to fault.",
                source="manual.md",
            )
        ]


class FakeLexical:
    async def lexical_search(self, vector, top_k):
        return [Chunk(chunk_id="l1", text="Check EtherCAT wiring.", source="alarms.md")]


class FakeReranker:
    async def rerank(self, query, chunks, effort):
        return chunks[: effort.reranker_n]


class FakeGenerator:
    async def generate(self, prompt, tokens=None, thinking=False, deterministic=False):       
        # uncited CAUSE: the fake can't know chunk order, so it's matched against all
        return (
            "COVERAGE: partial\n"
            "Try step 1, then step 2.\n"
            "CAUSE: A loose EtherCAT cable causes the drive to fault."
        )
    


class FakePreprocessor:
    async def process_prompt(self, raw_query, conversation_id, effort):
        return raw_query

    def store_context(self, conversation_id, query, response, alarm):
        return


def _fake_orchestrator() -> Orchestrator:
    retriever = HybridRetriever(
        FakeDenseEmbedder(), FakeSparseEmbedder(), FakeVectorStore(), FakeLexical()
    )
    return Orchestrator(
        FakePreprocessor(), retriever, FakeReranker(), FakeGenerator(), FakeAlarmStore()
    )


@pytest.fixture(autouse=True)
def _local_env_does_not_reach_tests(monkeypatch):
    # a developer's .env may turn it on, and the fake answers in these tests are not
    # written against the fake chunks; a test of the floor sets it itself
    monkeypatch.setenv("STEP_SUPPORT_MIN", "0")
    monkeypatch.setattr(get_settings(), "step_support_min", 0.0)
    # likewise the retrieval setup: a test of dual retrieval selects it itself
    monkeypatch.setenv("EMBEDDING_SETUP", "unified")
    monkeypatch.setattr(get_settings(), "embedding_setup", "unified")
    # and anonymous access: a request with no token is a 401 unless a test turns it on
    monkeypatch.setenv("ALLOW_ANONYMOUS_OPERATOR", "false")
    monkeypatch.setattr(get_settings(), "allow_anonymous_operator", False)
    # and the prompt capture for eval/diagnose_gaps.py
    monkeypatch.setenv("RESOLVE_DEBUG_PROMPT", "false")
    monkeypatch.setattr(get_settings(), "resolve_debug_prompt", False)


@pytest.fixture
def client():
    app.dependency_overrides[get_orchestrator] = _fake_orchestrator
    app.state.rate_limit_backend = FakeRateLimitBackend()
    yield TestClient(app)
    app.dependency_overrides.clear()
    if hasattr(app.state, "rate_limit_backend"):
        del app.state.rate_limit_backend


@pytest.fixture
def bearer():
    token, _ = create_access_token(user_id=1, tier=Tier.technician)
    return {"Authorization": f"Bearer {token}"}
