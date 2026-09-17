import jwt
import pytest

from rag_engine.api.errors import Unauthorized
from rag_engine.api.schemas import ChatRequest, ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token, decode_access_token
from rag_engine.config import get_settings
from rag_engine.orchestrator import Orchestrator


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_decode_token_accepts_valid_worker_tier():
    token, _ = create_access_token(user_id=42, tier=Tier.technician)

    principal = decode_access_token(token)

    assert principal.subject == "42"
    assert principal.tier == Tier.technician


def test_decode_token_rejects_invalid_tier():
    settings = get_settings()
    token, _ = create_access_token(user_id=42, tier=Tier.technician)
    claims = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
        audience=settings.jwt_audience,
    )
    claims["tier"] = "not-a-tier"
    forged = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    with pytest.raises(Unauthorized):
        decode_access_token(forged)


def test_orchestrator_resolve_uses_query_and_returns_top_results():
    class FakeReranker:
        async def rerank(self, query, chunks, top_n):
            return chunks[:top_n]

    class FakeRetriever:
        async def retrieve(self, query, top_k, where=None):
            return [
                type("Chunk", (), {"text": "Step 1", "source": "manual.md", "chunk_id": "c1", "score": 0.91})(),
                type("Chunk", (), {"text": "Step 2", "source": "manual.md", "chunk_id": "c2", "score": 0.81})(),
            ]

    class FakeGenerator:
        async def generate(self, prompt):
            return "answer"

    req = ResolveRequest(code="am.fb.0002", query="motor stalls after startup", env={"machine_variant": "X"})
    orch = Orchestrator(FakeRetriever(), FakeReranker(), FakeGenerator())

    response = pytest.importorskip("asyncio").run(orch.resolve(req, Tier.technician))

    assert response.code == "am.fb.0002"
    assert response.steps[0] == "Step 1"
    assert response.citations[0].chunk_id == "c1"
    assert response.confidence == 0.91


def test_orchestrator_chat_returns_retrieved_citations():
    class FakeReranker:
        async def rerank(self, query, chunks, top_n):
            return chunks[:top_n]

    class FakeRetriever:
        async def retrieve(self, query, top_k, where=None):
            return [
                type("Chunk", (), {"text": "text", "source": "faq.md", "chunk_id": "c1", "score": 0.5})(),
            ]

    class FakeGenerator:
        async def generate(self, prompt):
            return "final reply"

    req = ChatRequest(conversation_id="c-1", message="what happened?")
    orch = Orchestrator(FakeRetriever(), FakeReranker(), FakeGenerator())

    response = pytest.importorskip("asyncio").run(orch.chat(req, Tier.partner))

    assert response.conversation_id == "c-1"
    assert response.reply == "final reply"
    assert response.citations[0].chunk_id == "c1"
