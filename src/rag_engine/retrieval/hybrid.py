"""Hybrid retrieval: dense (pgvector) + lexical (BM25) fused with RRF."""
from rag_engine.retrieval.interfaces import (
    Chunk,
    Embedder,
    LexicalIndex,
    VectorStore,
)


def reciprocal_rank_fusion(
    rankings: list[list[Chunk]], k: int = 60
) -> list[Chunk]:
    """Fuse multiple ranked lists. Pure function -> fully unit-testable."""
    scores: dict[str, float] = {}
    by_id: dict[str, Chunk] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            by_id[chunk.chunk_id] = chunk
    fused = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    out = []
    for chunk_id, score in fused:
        c = by_id[chunk_id]
        c.score = score
        out.append(c)
    return out


class HybridRetriever:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        lexical: LexicalIndex,
        rrf_k: int = 60,
    ):
        self._embedder = embedder
        self._vs = vector_store
        self._lex = lexical
        self._rrf_k = rrf_k

    async def retrieve(
        self, query: str, top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]:
        vector = (await self._embedder.embed([query]))[0]
        dense = await self._vs.search(vector, top_k=top_k, where=where)
        sparse = await self._lex.search(query, top_k=top_k)
        return reciprocal_rank_fusion([dense, sparse], k=self._rrf_k)
