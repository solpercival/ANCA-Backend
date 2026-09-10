"""Coordinates a single resolve/chat turn across the retrieval components.

Onboarding note:
- this is the main runtime orchestration layer for a single request turn
- the app is designed to keep retrieval and generation behind interfaces, but the
  concrete runtime wiring is still the main integration task left to finish
- current status: tests use fake implementations; production wiring still needs a
  valid vector store, lexical index, and provider-backed generation path
- follow-up work: replace placeholder runtime objects with real Postgres/BM25
  integrations and validate a full end-to-end query path
"""
from rag_engine.api.auth import Tier
from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    ResolveRequest,
    ResolveResponse,
)
from rag_engine.providers import get_generation_backend
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.interfaces import Chunk, Generator, Reranker


class Orchestrator:
    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: Reranker,
        generator: Generator,
        rerank_top_n: int = 8,
        retrieval_top_k: int = 50,
    ):
        self._retriever = retriever
        self._reranker = reranker
        self._generator = generator
        self._top_n = rerank_top_n
        self._top_k = retrieval_top_k

    def _build_prompt(self, req: ResolveRequest, chunks: list[Chunk], tier: Tier) -> str:
        context = "\n\n".join(f"[{c.source}#{c.chunk_id}] {c.text}" for c in chunks)
        return (
            "You are a CNC troubleshooting assistant. Answer ONLY from the context. "
            "Produce ordered steps with citations; if the fix is not in the context, "
            f"say so.\nTier: {tier.value}\nAlarm: {req.code}\n\nContext:\n{context}"
        )

    async def resolve(self, req: ResolveRequest, tier: Tier) -> ResolveResponse:
        where = {}
        if req.env.machine_variant:
            where["machine_variant"] = req.env.machine_variant
        query = req.query or req.code
        candidates = await self._retriever.retrieve(query, top_k=self._top_k, where=where or None)
        top = await self._reranker.rerank(query, candidates, top_n=self._top_n)
        _ = self._build_prompt(req, top, tier)  # fed to generator in the real impl
        # Placeholder assembly; real generation happens in the model container.
        return ResolveResponse(
            code=req.code,
            steps=[c.text for c in top[:3]],
            citations=[Citation(source=c.source, chunk_id=c.chunk_id) for c in top[:3]],
            confidence=top[0].score if top else 0.0,
        )

    async def chat(self, req: ChatRequest, tier: Tier) -> ChatResponse:
        # Rewrite + session handling live here in the full build.
        candidates = await self._retriever.retrieve(req.message, top_k=self._top_k)
        top = await self._reranker.rerank(req.message, candidates, top_n=self._top_n)
        reply = await self._generator.generate(req.message)
        return ChatResponse(
            conversation_id=req.conversation_id,
            reply=reply,
            citations=[Citation(source=c.source, chunk_id=c.chunk_id) for c in top[:3]],
        )


def get_orchestrator() -> Orchestrator:  # pragma: no cover - wired at runtime
    """Real wiring. Switches the generation backend based on the configured provider."""
    from rag_engine.providers import get_embedding_backend
    from rag_engine.retrieval.hybrid import HybridRetriever

    embedder = get_embedding_backend()
    vector_store = None
    lexical = None
    retriever = HybridRetriever(embedder, vector_store, lexical)
    return Orchestrator(retriever, reranker=None, generator=get_generation_backend())
