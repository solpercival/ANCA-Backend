"""Coordinates a single resolve/chat turn across the retrieval components.

Onboarding note:
- this is the main runtime orchestration layer for a single request turn
- retrieval and generation stay behind interfaces; runtime wiring is the last
  integration task
- current status: tests use fakes; production wiring needs a valid vector store,
  lexical index, and provider-backed generation path
"""
from functools import lru_cache
from typing import Any

from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    ResolveRequest,
    ResolveResponse,
)
from rag_engine.auth.tiers import Tier
from rag_engine.config import get_settings
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.interfaces import Chunk, Generator, Reranker
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker
from rag_engine.stores.search import PostgresDBConnection


def get_vector_store_backend() -> Any:
    return PostgresDBConnection()


def get_reranker_backend() -> Reranker:
    """Build the configured reranker backend."""
    if get_settings().rerank_provider == "none":
        return IdentityReranker()
    return Qwen3Reranker()


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

    def _build_chat_prompt(self, message: str, chunks: list[Chunk]) -> str:
        context = "\n\n".join(f"[{c.source}#{c.chunk_id}] {c.text}" for c in chunks)
        return (
            "You are a CNC troubleshooting assistant. Answer the user's question "
            "using only the retrieved context. If the answer is not in the context, "
            f"say so.\n\nContext:\n{context}\n\nUser: {message}"
        )

    async def resolve(self, req: ResolveRequest, tier: Tier) -> ResolveResponse:
        where = {}
        if req.env.machine_variant:
            where["machine_variant"] = req.env.machine_variant
        query = req.query or req.code
        candidates = await self._retriever.retrieve(query, top_k=self._top_k, where=where or None)
        top = await self._reranker.rerank(query, candidates, top_n=self._top_n)
        answer = await self._generator.generate(self._build_prompt(req, top, tier))
        return ResolveResponse(
            code=req.code,
            steps=[answer],
            citations=[Citation(source=c.source, chunk_id=c.chunk_id) for c in top[:3]],
            tier=tier,
            confidence=top[0].score if top else 0.0,
        )

    async def chat(self, req: ChatRequest, tier: Tier) -> ChatResponse:
        candidates = await self._retriever.retrieve(req.message, top_k=self._top_k)
        top = await self._reranker.rerank(req.message, candidates, top_n=self._top_n)
        reply = await self._generator.generate(self._build_chat_prompt(req.message, top))
        return ChatResponse(
            conversation_id=req.conversation_id,
            reply=reply,
            citations=[Citation(source=c.source, chunk_id=c.chunk_id) for c in top[:3]],
        )


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:  # pragma: no cover - wired at runtime
    from rag_engine.main import app

    client = app.state.httpx_client

    from rag_engine.providers import (
        get_dense_embedding_backend,
        get_generation_backend,
        get_lexical_backend,
        get_sparse_embedding_backend,
    )

    dense_embedder = get_dense_embedding_backend(client=client)
    sparse_embedder = get_sparse_embedding_backend(client=client)
    vector_store = get_vector_store_backend()
    lexical = get_lexical_backend()
    retriever = HybridRetriever(dense_embedder, sparse_embedder, vector_store, lexical)
    return Orchestrator(
        retriever,
        reranker=get_reranker_backend(),
        generator=get_generation_backend(client=client),
    )