"""Dense or hybrid retrieval, depending on the embedding setup."""
import logging
import time

from rag_engine.config import get_settings
from rag_engine.retrieval.interfaces import (
    Chunk,
    DenseEmbedder,
    SparseEmbedder,
    LexicalIndex,
    VectorStore,
)

log = logging.getLogger("rag_engine.retrieval.hybrid")


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
        dense_embedder: DenseEmbedder,
        sparse_embedder: SparseEmbedder | None,
        vector_store: VectorStore,
        lexical: LexicalIndex | None,
        rrf_k: int = 60,
    ):
        self._dense_embedder = dense_embedder
        self._sparse_embedder = sparse_embedder
        self._vs = vector_store
        self._lex = lexical
        self._rrf_k = rrf_k

    async def retrieve(
        self, query: str, top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]:
        t0 = time.perf_counter()
        dense_vector = (await self._dense_embedder.dense_embed([query]))[0]
        t_embed = time.perf_counter() - t0

        t0 = time.perf_counter()
        dense = await self._vs.semantic_search(dense_vector, top_k=top_k, where=where)
        t_search = time.perf_counter() - t0

        if get_settings().embedding_setup != "dual":
            log.info("retrieve_timing embed=%.4fs search=%.4fs", t_embed, t_search)
            return dense

        if self._sparse_embedder is None or self._lex is None:
            raise RuntimeError("Dual retrieval requires sparse and lexical backends")

        t0 = time.perf_counter()
        sparse_vector = await self._sparse_embedder.sparse_embed([query])
        t_embed += time.perf_counter() - t0

        t0 = time.perf_counter()
        sparse = await self._lex.lexical_search(sparse_vector, top_k=top_k, where=where)
        t_search += time.perf_counter() - t0

        log.info("retrieve_timing embed=%.4fs search=%.4fs", t_embed, t_search)
        return reciprocal_rank_fusion([dense, sparse], k=self._rrf_k)