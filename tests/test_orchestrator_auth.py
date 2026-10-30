"""Token decoding, the reranker factory, and resolve/chat through the
orchestrator with fake backends.
"""

import jwt
import pytest

from rag_engine.api.errors import Unauthorized
from rag_engine.api.schemas import ChatRequest, ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token, decode_access_token
from rag_engine.config import get_settings
from rag_engine.orchestrator import Orchestrator, get_reranker_backend
from rag_engine.retrieval.doc_refs import DOCS_ROOT
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker
from tests.fakes import FakeAlarmStore


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
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        audience=settings.jwt_audience,
    )
    claims["tier"] = "not-a-tier"
    forged = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    with pytest.raises(Unauthorized):
        decode_access_token(forged)


@pytest.mark.parametrize(
    ("provider", "expected_type"),
    [("none", IdentityReranker), ("qwen3", Qwen3Reranker)],
)
def test_reranker_backend_factory_uses_configured_provider(monkeypatch, provider, expected_type):
    monkeypatch.setenv("RERANK_PROVIDER", provider)

    assert isinstance(get_reranker_backend(), expected_type)


@pytest.mark.parametrize("provider", [" QWEN3 ", "Qwen3", "None"])
def test_reranker_backend_factory_tolerates_case_and_whitespace(monkeypatch, provider):
    monkeypatch.setenv("RERANK_PROVIDER", provider)

    expected = IdentityReranker if provider.strip().lower() == "none" else Qwen3Reranker
    assert isinstance(get_reranker_backend(), expected)


def test_reranker_backend_reads_whole_chunks_by_default(monkeypatch):
    """The default must be long enough that a long table is not scored on its
    header rows alone (512 was not)."""
    monkeypatch.setenv("RERANK_PROVIDER", "qwen3")
    monkeypatch.delenv("RERANK_MAX_LENGTH", raising=False)

    assert get_reranker_backend()._max_length == 2048


def test_reranker_backend_uses_configured_max_length(monkeypatch):
    monkeypatch.setenv("RERANK_PROVIDER", "qwen3")
    monkeypatch.setenv("RERANK_MAX_LENGTH", "1024")

    assert get_reranker_backend()._max_length == 1024


@pytest.mark.parametrize("provider", ["qwn3", "qwen", "identity", ""])
def test_reranker_backend_factory_rejects_unknown_provider(monkeypatch, provider):
    monkeypatch.setenv("RERANK_PROVIDER", provider)

    with pytest.raises(ValueError, match="Unknown RERANK_PROVIDER"):
        get_reranker_backend()


def test_orchestrator_resolve_uses_query_and_returns_top_results():
    class FakePreprocessor:
        async def process_prompt(self, query, conversation_id, effort):
            return query

        def store_context(self, conversation_id, query, response, alarm):
            return

    class FakeReranker:
        async def rerank(self, query, chunks, effort):
            return chunks[: effort.reranker_n]

    class FakeRetriever:
        async def retrieve(self, query, top_k, where=None):
            return [
                Chunk(
                    chunk_id="c1",
                    text="Step 1",
                    source=f"{DOCS_ROOT}user-guide/a.md",
                    section="Drives",
                ),
                Chunk(chunk_id="c2", text="Step 2", source=f"{DOCS_ROOT}user-guide/a.md"),
            ]

    class FakeGenerator:
        prompt = None
        calls = 0

        async def generate(self, prompt, tokens=None, thinking=False, deterministic=False):
            self.calls += 1
            self.prompt = prompt
            return "answer"

    req = ResolveRequest(
        code="am.fb.0002",
        query="motor stalls after startup",
        env={"machine_variant": "X"},
    )
    orch = Orchestrator(
        FakePreprocessor(), FakeRetriever(), FakeReranker(), FakeGenerator(), FakeAlarmStore()
    )

    response = pytest.importorskip("asyncio").run(orch.resolve(req, Tier.technician))

    assert response.code == "am.fb.0002"
    assert response.steps == ["answer"]
    # contract shape: display name, bundle-relative path, heading; no local prefix or
    # chunk number. The second chunk has no heading, so it is its own citation
    assert [c.model_dump() for c in response.citations] == [
        {"doc": "AMCore User Guide", "path": "user-guide/a.md", "section": "Drives"},
        {"doc": "AMCore User Guide", "path": "user-guide/a.md", "section": None},
    ]
    assert response.doc_coverage == "partial"  # no COVERAGE header from the fake
    assert response.confidence == 0.5
    assert orch._generator.calls == 1
    assert "am.fb.0002" in orch._generator.prompt
    assert "Step 1" in orch._generator.prompt


def test_orchestrator_chat_returns_retrieved_citations():
    class FakePreprocessor:
        async def process_prompt(self, query, conversation_id, effort):
            return query

        def store_context(self, conversation_id, query, response, alarm):
            return

    class FakeReranker:
        async def rerank(self, query, chunks, effort):
            return chunks[: effort.reranker_n]

    class FakeRetriever:
        async def retrieve(self, query, top_k, where=None):
            return [Chunk(chunk_id="c1", text="text", source="faq.md", score=0.5)]

    class FakeGenerator:
        prompt = None
        calls = 0

        async def generate(self, prompt, tokens=None, thinking=False, deterministic=False):
            self.calls += 1
            self.prompt = prompt
            return "final reply"

    req = ChatRequest(conversation_id="c-1", message="what happened?")
    orch = Orchestrator(
        FakePreprocessor(), FakeRetriever(), FakeReranker(), FakeGenerator(), FakeAlarmStore()
    )

    response = pytest.importorskip("asyncio").run(orch.chat(req, Tier.partner))

    assert response.conversation_id == "c-1"
    assert response.reply == "final reply"
    assert orch._generator.calls == 1
    assert [c.model_dump() for c in response.citations] == [
        {"doc": "Documentation", "path": "faq.md", "section": None}
    ]
    assert "what happened?" in orch._generator.prompt
    assert "text" in orch._generator.prompt
