import pytest
from fastapi.testclient import TestClient

from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.main import app
from rag_engine.orchestrator import Orchestrator, get_orchestrator
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.interfaces import Chunk


class FakeEmbedder:
    async def embed(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeVectorStore:
    async def search(self, vector, top_k, where=None):
        return [Chunk(chunk_id="v1", text="Reset the drive.", source="manual.md")]

class FakeLexical:
    async def search(self, query, top_k):
        return [Chunk(chunk_id="l1", text="Check EtherCAT wiring.", source="alarms.md")]


class FakeReranker:
    async def rerank(self, query, chunks, top_n):
        return chunks[:top_n]


class FakeGenerator:
    async def generate(self, prompt):
        return "Try step 1, then step 2."


def _fake_orchestrator() -> Orchestrator:
    retriever = HybridRetriever(FakeEmbedder(), FakeVectorStore(), FakeLexical())
    return Orchestrator(retriever, FakeReranker(), FakeGenerator())


@pytest.fixture
def client():
    app.dependency_overrides[get_orchestrator] = _fake_orchestrator
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def bearer():
    token, _ = create_access_token(user_id=1, tier=Tier.technician)
    return {"Authorization": f"Bearer {token}"}
