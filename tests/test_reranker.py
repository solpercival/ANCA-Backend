"""Tests for the placeholder reranker."""
from rag_engine.retrieval.interfaces import Chunk, Reranker
from rag_engine.retrieval.reranker import IdentityReranker


def _chunks(n: int) -> list[Chunk]:
    return [
        Chunk(chunk_id=str(i), text=f"chunk {i}", source="test.md")
        for i in range(n)
    ]


def test_satisfies_protocol() -> None:
    """The class structurally matches the Reranker protocol."""
    reranker: Reranker = IdentityReranker()
    assert reranker is not None


async def test_truncates_and_preserves_order() -> None:
    """Ten chunks in, first five out, order unchanged."""
    result = await IdentityReranker().rerank("any query", _chunks(10), top_n=5)
    assert [c.chunk_id for c in result] == ["0", "1", "2", "3", "4"]


async def test_empty_input_returns_empty() -> None:
    """An empty candidate list comes back empty."""
    assert await IdentityReranker().rerank("any query", [], top_n=5) == []