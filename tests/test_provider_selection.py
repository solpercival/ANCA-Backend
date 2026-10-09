"""Provider factories and adapters (providers.py) against mocked HTTP:
settings overrides, backend selection, Ollama request options and timing logs,
plus reciprocal rank fusion and the hybrid retriever.
"""
import asyncio
import httpx
import pytest

from rag_engine.config import get_settings
from rag_engine.providers import (
    AnthropicGenerator,
    OllamaEmbedder,
    OllamaGenerator,
    OpenAIEmbedder,
    OpenAIGenerator,
    TEIEmbedder,
    get_sparse_embedding_backend,
    get_dense_embedding_backend,
    get_generation_backend,
)
from rag_engine.retrieval.hybrid import HybridRetriever, reciprocal_rank_fusion
from rag_engine.retrieval.interfaces import Chunk, DenseEmbedder, SparseEmbedder


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_env_overrides_are_applied(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "pg.example")
    monkeypatch.setenv("POSTGRES_DB", "rag_test")
    monkeypatch.setenv("DENSE_EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setenv("SPARSE_EMBEDDING_PROVIDER", "huggingface_tei")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    settings = get_settings()

    assert settings.postgres_host == "pg.example"
    assert settings.postgres_db == "rag_test"
    assert settings.dense_embedding_provider == "ollama"
    assert settings.sparse_embedding_provider == "huggingface_tei"
    assert settings.llm_provider == "anthropic"
    assert settings.postgres_dsn.startswith("postgresql://")


@pytest.mark.parametrize(
    ("provider", "expected_type"),
    [("ollama", OllamaEmbedder), ("openai", OpenAIEmbedder)],
)
def test_dense_embedding_backend_factory_returns_expected_provider(monkeypatch, provider, expected_type):
    monkeypatch.setenv("DENSE_EMBEDDING_PROVIDER", provider)

    with httpx.Client(timeout=120.0) as client: 
        backend = get_dense_embedding_backend(client)

    assert isinstance(backend, expected_type)


@pytest.mark.parametrize(("env", "expected"), [(None, 1024), ("512", 512)])
def test_ollama_embedder_sends_small_num_ctx(monkeypatch, env, expected):
    # Ollama's default 4096 ctx made the embedder hold ~2.4 GB of VRAM
    import json

    if env:
        monkeypatch.setenv("EMBEDDING_NUM_CTX", env)
    else:
        monkeypatch.delenv("EMBEDDING_NUM_CTX", raising=False)
    sent = {}

    def handler(request):
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await OllamaEmbedder(client).dense_embed(["query"])

    assert asyncio.run(run()) == [[0.1, 0.2]]
    assert sent["options"]["num_ctx"] == expected
    assert sent["input"] == ["query"]


def test_ollama_generator_logs_prompt_and_output_timing(caplog):
    import json

    lines = [
        {"response": "COVERAGE: partial\n", "done": False},
        {"response": "Check the cable.", "done": False},
        {
            "response": "", "done": True, "done_reason": "length",
            "prompt_eval_count": 3000, "prompt_eval_duration": 2_000_000_000,
            "eval_count": 180, "eval_duration": 6_000_000_000,
            "load_duration": 50_000_000, "total_duration": 8_100_000_000,
        },
    ]
    body = "\n".join(json.dumps(x) for x in lines)

    async def run():
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body))
        async with httpx.AsyncClient(transport=transport) as client:
            return await OllamaGenerator(client).generate("prompt", 200, False)

    with caplog.at_level("INFO", logger="rag_engine.providers"):
        reply = asyncio.run(run())

    assert reply == "COVERAGE: partial\nCheck the cable."
    stats = next(r.getMessage() for r in caplog.records if "generate_stats" in r.getMessage())
    assert "prompt_tokens=3000 prompt_secs=2.00 prompt_tok_s=1500" in stats
    assert "output_tokens=180 output_secs=6.00 output_tok_s=30.0" in stats
    assert "done_reason=length" in stats


@pytest.mark.parametrize(("env", "expected"), [(None, 0), ("99", 99)])
def test_ollama_query_embedder_defaults_to_cpu(monkeypatch, env, expected):
    # num_gpu=0 keeps the query embedder off the 6 GB GPU budget
    import json

    if env:
        monkeypatch.setenv("EMBEDDING_NUM_GPU", env)
    else:
        monkeypatch.delenv("EMBEDDING_NUM_GPU", raising=False)
    sent = {}

    def handler(request):
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"embeddings": [[0.1]]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await OllamaEmbedder(client).dense_embed(["query"])

    asyncio.run(run())
    assert sent["options"]["num_gpu"] == expected


def test_anthropic_embedding_provider_fails_at_factory(monkeypatch):
    monkeypatch.setenv("DENSE_EMBEDDING_PROVIDER", "anthropic")

    with httpx.Client(timeout=120.0) as client:
        with pytest.raises(ValueError, match="Anthropic does not provide embeddings"):
            get_dense_embedding_backend(client)

@pytest.mark.parametrize(
    ("provider", "expected_type"),
    [
        ("huggingface_tei", TEIEmbedder),
    ],
)
def test_dense_sparse_backend_factory_returns_expected_provider(monkeypatch, provider, expected_type):
    monkeypatch.setenv("SPARSE_EMBEDDING_PROVIDER", provider)
    
    with httpx.Client(timeout=120.0) as client:
        backend = get_sparse_embedding_backend(client)

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

    with httpx.Client(timeout=120.0) as client:
        backend = get_generation_backend(client)

    assert isinstance(backend, expected_type)


def test_invalid_provider_raises_value_error(monkeypatch):
    monkeypatch.setenv("DENSE_EMBEDDING_PROVIDER", "unsupported")
    monkeypatch.setenv("SPARSE_EMBEDDING_PROVIDER", "unsupported")
    monkeypatch.setenv("LLM_PROVIDER", "unsupported")

    with httpx.Client(timeout=120.0) as client:
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            get_dense_embedding_backend(client)

        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            get_sparse_embedding_backend(client)

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_generation_backend(client)


def test_reciprocal_rank_fusion_prefers_agreement_and_dedupes():
    a = Chunk(chunk_id="x", text="alpha", source="s1")
    b = Chunk(chunk_id="y", text="beta", source="s2")

    fused = reciprocal_rank_fusion([[a, b], [a, b]], k=60)

    assert fused[0].chunk_id == "x"
    assert len(fused) == 2
    assert len({chunk.chunk_id for chunk in fused}) == 2


def test_hybrid_retriever_uses_dense_and_lexical_lists(monkeypatch):
    monkeypatch.setenv("EMBEDDING_SETUP", "dual")
    class FakeDenseEmbedder:
        async def dense_embed(self, texts):
            return [[0.1, 0.2, 0.3] for _ in texts]

    class FakeSparseEmbedder:
        async def sparse_embed(self, texts):
            return [{2: 0.12, 93: 0.4367, 254: 0.111} for _ in texts]

    class FakeVectorStore:
        async def semantic_search(self, vector, top_k, where=None):
            return [
                Chunk(chunk_id="v1", text="dense_result", source="manual.md"),
                Chunk(chunk_id="v2", text="dense_result_two", source="manual.md"),
            ]

    class FakeLexical:
        async def lexical_search(self, query, top_k, where=None):
            return [
                Chunk(chunk_id="v1", text="dense_result", source="manual.md"),
                Chunk(chunk_id="l1", text="lexical_result", source="faq.md"),
            ]

    retriever = HybridRetriever(FakeDenseEmbedder(), FakeSparseEmbedder(), FakeVectorStore(), FakeLexical(), rrf_k=60)
    result = asyncio.run(retriever.retrieve("troubleshooting query", top_k=5))

    chunk_ids = {chunk.chunk_id for chunk in result}
    assert {"v1", "v2", "l1"}.issubset(chunk_ids)
    assert result[0].chunk_id in {"v1", "l1", "v2"}


def test_retriever_uses_dense_only_without_sparse_or_lexical(monkeypatch):
    monkeypatch.setenv("EMBEDDING_SETUP", "unified")

    class FakeDenseEmbedder:
        async def dense_embed(self, texts):
            return [[0.1, 0.2, 0.3] for _ in texts]

    class FailingSparseEmbedder:
        async def sparse_embed(self, texts):
            raise AssertionError("sparse embedding must not be called")

    class FailingLexical:
        async def lexical_search(self, vector, top_k):
            raise AssertionError("lexical search must not be called")

    class FakeVectorStore:
        async def semantic_search(self, vector, top_k, where=None):
            return [Chunk(chunk_id="dense", text="dense result", source="manual.md")]

    retriever = HybridRetriever(
        FakeDenseEmbedder(),
        FailingSparseEmbedder(),
        FakeVectorStore(),
        FailingLexical(),
    )

    result = asyncio.run(retriever.retrieve("dense query", top_k=5))

    assert [chunk.chunk_id for chunk in result] == ["dense"]

@pytest.mark.integration
async def test_dense_embedding_backend_output():
    settings = get_settings()
    with httpx.Client(timeout=120.0) as client:
        backend = get_dense_embedding_backend(client)
        assert backend is not None
        assert hasattr(backend, "dense_embed") and callable(backend.dense_embed)
        queries = ["test query 1", "anca motion"]
        embeddings = await backend.dense_embed(queries)
    assert len(embeddings) == 2
    assert embeddings[0] != embeddings[1]
    assert all(len(i) == settings.semantic_dim for i in embeddings)
    assert all(any(x != 0 for x in emb) for emb in embeddings)

@pytest.mark.integration
async def test_sparse_embedding_backend_output():
    settings = get_settings()
    with httpx.Client(timeout=120.0) as client:
        backend = get_sparse_embedding_backend(client)

        assert (backend != None)
        assert hasattr(backend, "sparse_embed") and callable(backend.sparse_embed)

        queries = ["test query 1", "anca motion"]
        embeddings = await backend.sparse_embed(queries)

    assert (len(embeddings) == 2)
    assert (embeddings[0] != embeddings[1])
    assert all(len(i) <= settings.lexical_dim for i in embeddings)
    assert all(len(i) > 0 for i in embeddings)
