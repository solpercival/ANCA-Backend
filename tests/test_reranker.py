"""Tests for the reranker implementations.

Qwen3Reranker's scoring is replaced with fixed fake scores, so the sorting and
truncation can be tested without loading the model.
"""

from rag_engine.retrieval.interfaces import Chunk
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker


def _chunks(n: int) -> list[Chunk]:
    return [
        Chunk(chunk_id=str(i), text=f"chunk {i}", source="test.md")
        for i in range(n)
    ]


async def test_identity_truncates_and_preserves_order() -> None:
    """Ten chunks in, first five out and the order is unchanged."""
    result = await IdentityReranker().rerank("any query", _chunks(10), top_n=5)
    assert [c.chunk_id for c in result] == ["0", "1", "2", "3", "4"]


async def test_identity_empty_input_returns_empty() -> None:
    """An empty candidate list comes back empty."""
    assert await IdentityReranker().rerank("any query", [], top_n=5) == []


async def test_qwen3_orders_by_score_and_truncates() -> None:
    """Chunks come back sorted by score truncated to top_n."""
    reranker = Qwen3Reranker()
    reranker._ensure_loaded = lambda: None  # type: ignore[method-assign]
    reranker._score = lambda query, texts: [  # type: ignore[method-assign]
        float(i) for i in range(len(texts) - 1, -1, -1)
    ]

    result = await reranker.rerank("any query", _chunks(10), top_n=3)

    assert [c.chunk_id for c in result] == ["0", "1", "2"]
    assert result[0].score == 9.0


async def test_qwen3_empty_input_returns_empty() -> None:
    """An empty candidate list comes back empty without loading the model."""
    assert await Qwen3Reranker().rerank("any query", [], top_n=5) == []