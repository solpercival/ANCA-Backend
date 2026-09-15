"""Placeholder implementation of the Reranker protocol.

Returns candidates in the order they arrived, truncated to top_n. This exists so
the retrieval pipeline can be wired and tested before a model is introduced, and
serves as the baseline the real reranker will be measured against.
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