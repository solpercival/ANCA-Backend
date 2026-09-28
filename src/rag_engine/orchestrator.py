"""Coordinates a single resolve/chat turn across the retrieval components.

Onboarding note:
- this is the main runtime orchestration layer for a single request turn
- retrieval and generation stay behind interfaces; runtime wiring is the last
  integration task
- current status: tests use fakes; production wiring needs a valid vector store,
  lexical index, and provider-backed generation path
"""
from functools import lru_cache
import logging
import re
import time
from typing import Any

from langfuse import Langfuse

from rag_engine.api.metrics import rag_stage_seconds, rag_resolve_total
from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    ResolveRequest,
    ResolveResponse,
)
from rag_engine.api.errors import ModelUnavailable, RetrievalUnavailable
from rag_engine.auth.tiers import Tier, can_view_likely_causes
from rag_engine.config import get_settings
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.interfaces import Chunk, Generator, Reranker
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker
from rag_engine.stores.search import PostgresDBConnection

log = logging.getLogger("rag_engine.orchestrator")

_NOT_COVERED = "The documentation does not cover this alarm."

# models sometimes number or bullet lines despite the prompt; strip that prefix
_STEP_PREFIX = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s*")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_CAUSE_HINT = re.compile(r"\b(caus\w*|due to|because|occurs? (?:when|if)|results? from)\b", re.I)
_MAX_CAUSES = 3
_MAX_CAUSE_CHARS = 200


def _get_langfuse_client() -> Langfuse | None:
    """Instantiate Langfuse client if configured, else None."""
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def get_vector_store_backend() -> Any:
    return PostgresDBConnection()


def get_reranker_backend() -> Reranker:
    """Build the configured reranker backend."""
    if get_settings().rerank_provider == "none":
        return IdentityReranker()
    return Qwen3Reranker(max_length=512)


def _log_candidates(candidates: list[Chunk]) -> None:
    # sanity check that retrieval returns usable text, not just ids/sources
    empty = sum(1 for c in candidates if not (c.text or "").strip())
    preview = candidates[0].text[:120].replace("\n", " ") if candidates else ""
    log.info("retrieved count=%d empty_text=%d first=%r", len(candidates), empty, preview)


class Orchestrator:
    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: Reranker,
        generator: Generator,
        rerank_top_n: int = 8,
        retrieval_top_k: int = 50,
        langfuse_client: Langfuse | None = None,
    ):
        self._retriever = retriever
        self._reranker = reranker
        self._generator = generator
        self._top_n = rerank_top_n
        self._top_k = retrieval_top_k
        self._langfuse = langfuse_client

    @staticmethod
    def _format_context(chunks: list[Chunk]) -> str:
        # short [n] labels so citations cost the model a few tokens, not a file path
        return "\n\n".join(f"[{i}] ({c.source}) {c.text}" for i, c in enumerate(chunks, 1))

    def _build_prompt(self, req: ResolveRequest, chunks: list[Chunk], tier: Tier) -> str:
        return (
            "You are a CNC troubleshooting assistant. Answer ONLY from the context.\n"
            "Output at most 5 steps, one step per line, no numbering or bullets, "
            "one short sentence each, citing sources as [n]. "
            "No introduction, no summary, no repetition of the question.\n"
            "If the fix is not in the context, reply exactly: "
            f"\"{_NOT_COVERED}\"\n"
            f"Tier: {tier.value}\nAlarm: {req.code}\n\nContext:\n{self._format_context(chunks)}"
        )

    @staticmethod
    def _split_steps(answer: str) -> list[str]:
        steps = [_STEP_PREFIX.sub("", ln).strip() for ln in answer.splitlines()]
        return [s for s in steps if s] or [answer.strip()]

    def _confidence(self, top: list[Chunk]) -> float:
        """Score in [0, 1] for the best chunk; 0.0 means "no calibrated signal".

        - IdentityReranker: chunk scores are raw RRF fusion values (~1/(60+rank)),
          which are ordinal only, so no confidence is claimed and 0.0 is returned.
        - Cross-encoder rerankers (Qwen3): score is P("yes") from a softmax, i.e.
          the model's estimated relevance of the top chunk to the query, clamped
          to [0, 1] defensively.
        """
        if not top or isinstance(self._reranker, IdentityReranker):
            return 0.0
        return min(1.0, max(0.0, float(top[0].score)))

    @staticmethod
    def _derive_likely_causes(chunks: list[Chunk]) -> list[str]:
        # Interim heuristic until causes come from the alarm record: take the most
        # cause-like sentence from each of the top chunks, falling back to its
        # first sentence. Ordered by rerank position, deduplicated.
        causes: list[str] = []
        for c in chunks[:_MAX_CAUSES]:
            sentences = [
                s.strip() for s in _SENTENCE_SPLIT.split(" ".join((c.text or "").split())) if s.strip()
            ]
            if not sentences:
                continue
            pick = next((s for s in sentences if _CAUSE_HINT.search(s)), sentences[0])
            if len(pick) > _MAX_CAUSE_CHARS:
                pick = pick[: _MAX_CAUSE_CHARS - 1].rstrip() + "…"
            if pick not in causes:
                causes.append(pick)
        return causes

    def _build_chat_prompt(self, message: str, chunks: list[Chunk]) -> str:
        return (
            "You are a CNC troubleshooting assistant. Answer the user's question using only "
            "the context, in at most 3 short sentences, citing sources as [n]. No preamble.\n"
            "If the answer is not in the context, reply exactly: "
            "\"The documentation does not cover this.\"\n\n"
            f"Context:\n{self._format_context(chunks)}\n\nUser: {message}"
        )

    async def resolve(self, req: ResolveRequest, tier: Tier) -> ResolveResponse:
        where = {}
        if req.env.versions:
            where["versions"] = req.env.versions
        if req.env.machine_variant:
            where["machine_variant"] = req.env.machine_variant
        query = req.query or req.code

        trace = None
        if self._langfuse:
            trace = self._langfuse.trace(name="resolve", input={"code": req.code, "query": query})

        t0 = time.perf_counter()
        try:
            candidates = await self._retriever.retrieve(query, top_k=self._top_k, where=where or None)
        except Exception as exc:
            log.exception("retrieval_error code=%s", req.code)
            rag_resolve_total.labels(outcome="error").inc()
            raise RetrievalUnavailable() from exc
        t_retrieve = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="retrieve").observe(t_retrieve)
        _log_candidates(candidates)

        if self._langfuse and trace:
            trace.span(
                name="retrieve",
                input={"query": query, "top_k": self._top_k, "where": where or None},
                output={"candidates_count": len(candidates)},
                duration_ms=int(t_retrieve * 1000),
            )

        trimmed = candidates[:20]

        t0 = time.perf_counter()
        top = await self._reranker.rerank(query, trimmed, top_n=self._top_n)
        t_rerank = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="rerank").observe(t_rerank)

        if self._langfuse and trace:
            trace.span(
                name="rerank",
                input={"candidates_count": len(candidates), "top_n": self._top_n},
                output={"top_count": len(top)},
                duration_ms=int(t_rerank * 1000),
            )

        t0 = time.perf_counter()
        try:
            answer = await self._generator.generate(self._build_prompt(req, top, tier))
        except Exception as exc:
            log.exception("generation_error code=%s", req.code)
            rag_resolve_total.labels(outcome="error").inc()
            raise ModelUnavailable() from exc
        t_generate = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="generate").observe(t_generate)

        if self._langfuse and trace:
            trace.span(
                name="generate",
                input={"top_chunks": len(top), "tier": tier.value},
                output={"answer_length": len(answer)},
                duration_ms=int(t_generate * 1000),
            )

        log.info(
            "resolve_timing code=%s retrieve=%.4fs rerank=%.4fs generate=%.4fs total=%.4fs",
            req.code, t_retrieve, t_rerank, t_generate, t_retrieve + t_rerank + t_generate,
        )

        if self._langfuse and trace:
            trace.update(
                output={
                    "code": req.code,
                    "citations_count": min(3, len(top)),
                    "total_latency_ms": int((t_retrieve + t_rerank + t_generate) * 1000),
                }
            )

        steps = self._split_steps(answer)
        # the route also strips causes per tier; skipping here just avoids the work.
        # No causes when the model found no fix, so we don't guess from weak chunks.
        covered = _NOT_COVERED.lower() not in answer.lower()
        likely_causes = (
            self._derive_likely_causes(top) if covered and can_view_likely_causes(tier) else []
        )

        rag_resolve_total.labels(outcome="ok").inc()
        return ResolveResponse(
            code=req.code,
            steps=steps,
            likely_causes=likely_causes,
            citations=[Citation(source=c.source, chunk_id=c.chunk_id) for c in top[:3]],
            tier=tier,
            confidence=self._confidence(top),
        )

    async def chat(self, req: ChatRequest, tier: Tier) -> ChatResponse:
        trace = None
        if self._langfuse:
            trace = self._langfuse.trace(name="chat", input={"conversation_id": req.conversation_id, "message": req.message})

        t0 = time.perf_counter()
        try:
            candidates = await self._retriever.retrieve(req.message, top_k=self._top_k)
        except Exception as exc:
            log.exception("retrieval_error conversation_id=%s", req.conversation_id)
            rag_resolve_total.labels(outcome="error").inc()
            raise RetrievalUnavailable() from exc
        t_retrieve = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="retrieve").observe(t_retrieve)
        _log_candidates(candidates)

        if self._langfuse and trace:
            trace.span(
                name="retrieve",
                input={"query": req.message, "top_k": self._top_k},
                output={"candidates_count": len(candidates)},
                duration_ms=int(t_retrieve * 1000),
            )

        trimmed = candidates[:20]

        t0 = time.perf_counter()
        top = await self._reranker.rerank(req.message, trimmed, top_n=self._top_n)
        t_rerank = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="rerank").observe(t_rerank)

        if self._langfuse and trace:
            trace.span(
                name="rerank",
                input={"candidates_count": len(candidates), "top_n": self._top_n},
                output={"top_count": len(top)},
                duration_ms=int(t_rerank * 1000),
            )

        t0 = time.perf_counter()
        try:
            reply = await self._generator.generate(self._build_chat_prompt(req.message, top))
        except Exception as exc:
            log.exception("generation_error conversation_id=%s", req.conversation_id)
            rag_resolve_total.labels(outcome="error").inc()
            raise ModelUnavailable() from exc
        t_generate = time.perf_counter() - t0
        rag_stage_seconds.labels(stage="generate").observe(t_generate)

        if self._langfuse and trace:
            trace.span(
                name="generate",
                input={"top_chunks": len(top)},
                output={"reply_length": len(reply)},
                duration_ms=int(t_generate * 1000),
            )

        if self._langfuse and trace:
            trace.update(
                output={
                    "conversation_id": req.conversation_id,
                    "citations_count": min(3, len(top)),
                    "total_latency_ms": int((t_retrieve + t_rerank + t_generate) * 1000),
                }
            )

        rag_resolve_total.labels(outcome="ok").inc()
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
    vector_store = get_vector_store_backend()
    if get_settings().embedding_setup == "dual":
        sparse_embedder = get_sparse_embedding_backend(client=client)
        lexical = get_lexical_backend()
    else:
        sparse_embedder = None
        lexical = None
    retriever = HybridRetriever(dense_embedder, sparse_embedder, vector_store, lexical)
    return Orchestrator(
        retriever,
        reranker=get_reranker_backend(),
        generator=get_generation_backend(client=client),
        langfuse_client=_get_langfuse_client(),
    )