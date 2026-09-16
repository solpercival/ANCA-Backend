"""Placeholder reranker.

Returns the first top_n chunks unchanged, without scoring them. 
Gives a baseline to compare the real reranker against.
"""
from rag_engine.retrieval.interfaces import Chunk


class IdentityReranker:
    """No-op reranker: preserves incoming order, truncates to top_n."""

    async def rerank(
        self, query: str, chunks: list[Chunk], top_n: int
    ) -> list[Chunk]:
        """Return the first top_n chunks unchanged."""
        del query  # unused: ordering is left to the caller
        return list(chunks[:top_n])