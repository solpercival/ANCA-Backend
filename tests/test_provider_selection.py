import asyncio

import pytest

from rag_engine.config import get_settings
from rag_engine.providers import (
    AnthropicEmbedder,
    AnthropicGenerator,
    OllamaEmbedder,
    OllamaGenerator,
    OpenAIEmbedder,
    OpenAIGenerator,
    get_embedding_backend,
    get_generation_backend,
)
from rag_engine.retrieval.hybrid import HybridRetriever, reciprocal_rank_fusion
from rag_engine.retrieval.interfaces import Chunk


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_env_overrides_are_applied(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "pg.example")
    monkeypatch.setenv("POSTGRES_DB", "rag_test")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    settings = get_settings()

    assert settings.postgres_host == "pg.example"
    assert settings.postgres_db == "rag_test"
    assert settings.embedding_provider == "openai"
    assert settings.llm_provider == "anthropic"
    assert settings.postgres_dsn.startswith("postgresql://")


@pytest.mark.parametrize(
    ("provider", "expected_type"),
    [
        ("ollama", OllamaEmbedder),
        ("openai", OpenAIEmbedder),
        ("anthropic", AnthropicEmbedder),
    ],
)
def test_embedding_backend_factory_returns_expected_provider(monkeypatch, provider, expected_type):
    monkeypatch.setenv("EMBEDDING_PROVIDER", provider)
    backend = get_embedding_backend()
    assert isinstance(backend, expected_type)


@pytest.mark.parametrize(
    ("provider", "expected_type"),
    [
        ("ollama", OllamaGenerator),
        ("openai", OpenAIGenerator),
        ("anthropic", AnthropicGenerator),
    ],
)
def test_generation_backend_factory_returns_expected_provider(monkeypatch, provider, expected_type):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    backend = get_generation_backend()
    assert isinstance(backend, expected_type)


def test_invalid_provider_raises_value_error(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "unsupported")
    monkeypatch.setenv("LLM_PROVIDER", "unsupported")

    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        get_embedding_backend()

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_generation_backend()


def test_reciprocal_rank_fusion_prefers_agreement_and_dedupes():
    a = Chunk(chunk_id="x", text="alpha", source="s1")
    b = Chunk(chunk_id="y", text="beta", source="s2")

    fused = reciprocal_rank_fusion([[a, b], [a, b]], k=60)

    assert fused[0].chunk_id == "x"
    assert len(fused) == 2
    assert len({chunk.chunk_id for chunk in fused}) == 2


def test_hybrid_retriever_uses_dense_and_lexical_lists():
    class FakeEmbedder:
        async def embed(self, texts):
            return [[0.1, 0.2, 0.3] for _ in texts]

    class FakeVectorStore:
        async def search(self, vector, top_k, where=None):
            return [
                Chunk(chunk_id="v1", text="dense_result", source="manual.md"),
                Chunk(chunk_id="v2", text="dense_result_two", source="manual.md"),
            ]

    class FakeLexical:
        async def search(self, query, top_k):
            return [
                Chunk(chunk_id="v1", text="dense_result", source="manual.md"),
                Chunk(chunk_id="l1", text="lexical_result", source="faq.md"),
            ]

    retriever = HybridRetriever(FakeEmbedder(), FakeVectorStore(), FakeLexical(), rrf_k=60)
    result = asyncio.run(retriever.retrieve("troubleshooting query", top_k=5))

    chunk_ids = {chunk.chunk_id for chunk in result}
    assert {"v1", "v2", "l1"}.issubset(chunk_ids)
    assert result[0].chunk_id in {"v1", "l1", "v2"}
