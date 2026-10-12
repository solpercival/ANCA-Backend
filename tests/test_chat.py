"""Orchestrator.chat with in-process fakes: query rewriting, effort-dependent
retrieval and reranking, the chat prompt, citation handling, conversation storage,
and the errors raised when retrieval or generation fails. No services needed."""

import asyncio

import pytest

from rag_engine.api.errors import ModelUnavailable, RetrievalUnavailable
from rag_engine.api.schemas import ChatRequest, EffortLevel
from rag_engine.auth.tiers import Tier
from rag_engine.orchestrator import Orchestrator
from rag_engine.retrieval.interfaces import Chunk
from tests.fakes import FakeAlarmStore


class RecordingPreprocessor:
    """Rewrites every message to `rewrite` and records each call."""

    def __init__(self, rewrite="standalone query"):
        self._rewrite = rewrite
        self.process_calls = []
        self.stored = []

    async def process_prompt(self, raw_query, conversation_id, effort):
        self.process_calls.append((raw_query, conversation_id))
        return self._rewrite

    def store_context(self, conversation_id, query, response, alarm):
        self.stored.append((conversation_id, query, response, alarm))


class RecordingRetriever:
    def __init__(self, chunks=None, error=None):
        self._chunks = chunks if chunks is not None else _chunks(2)
        self._error = error
        self.calls = []

    async def retrieve(self, query, top_k, where=None):
        self.calls.append((query, top_k, where))
        if self._error:
            raise self._error
        return self._chunks


class RecordingReranker:
    def __init__(self):
        self.calls = []

    async def rerank(self, query, chunks, effort):
        self.calls.append((query, list(chunks)))
        return chunks[: effort.reranker_n]


class RecordingGenerator:
    def __init__(self, reply="Reset the drive from the HMI.", error=None):
        self._reply = reply
        self._error = error
        self.prompts = []

    async def generate(self, prompt, tokens=None, thinking=False):
        self.prompts.append(prompt)
        if self._error:
            raise self._error
        return self._reply


def _chunks(n):
    return [
        Chunk(chunk_id=f"c{i}", text=f"Doc text {i}.", source=f"doc{i}.md", score=1.0 - i / 100)
        for i in range(n)
    ]


def _orch(preprocessor=None, retriever=None, reranker=None, generator=None):
    return Orchestrator(
        preprocessor or RecordingPreprocessor(),
        retriever or RecordingRetriever(),
        reranker or RecordingReranker(),
        generator or RecordingGenerator(),
        FakeAlarmStore(),
    )


def _chat(orch, message="how do I fix it?", effort=EffortLevel.MEDIUM, tier=Tier.technician):
    req = ChatRequest(conversation_id="conv-1", message=message, effort=effort)
    return asyncio.run(orch.chat(req, tier))


# --- query rewriting -------------------------------------------------------


def test_rewritten_query_is_what_gets_retrieved_reranked_and_prompted():
    pre, ret, rer, gen = (
        RecordingPreprocessor("standalone query"),
        RecordingRetriever(),
        RecordingReranker(),
        RecordingGenerator(),
    )
    _chat(_orch(pre, ret, rer, gen), message="how do I fix it?")

    assert pre.process_calls == [("how do I fix it?", "conv-1")]
    assert ret.calls[0][0] == "standalone query"
    assert rer.calls[0][0] == "standalone query"
    assert "User: standalone query" in gen.prompts[0]


def test_low_effort_skips_the_rewrite():
    pre, ret = RecordingPreprocessor("should not be used"), RecordingRetriever()
    _chat(_orch(pre, ret), message="raw message", effort=EffortLevel.LOW)

    assert pre.process_calls == []
    assert ret.calls[0][0] == "raw message"


def test_empty_rewrite_returns_empty_reply_without_retrieval_or_generation():
    pre, ret, gen = RecordingPreprocessor(""), RecordingRetriever(), RecordingGenerator()
    resp = _chat(_orch(pre, ret, generator=gen))

    assert resp.conversation_id == "conv-1"
    assert resp.reply == ""
    assert resp.citations == []
    assert ret.calls == []
    assert gen.prompts == []
    assert pre.stored == []


# --- retrieval and reranking per effort ------------------------------------


@pytest.mark.parametrize(
    ("effort", "top_k", "context_k"),
    [(EffortLevel.MEDIUM, 50, 10), (EffortLevel.HIGH, 80, 30)],
)
def test_retrieval_k_and_context_trim_follow_effort(effort, top_k, context_k):
    ret, rer = RecordingRetriever(_chunks(40)), RecordingReranker()
    _chat(_orch(retriever=ret, reranker=rer), effort=effort)

    assert ret.calls[0][1] == top_k
    assert ret.calls[0][2] is None  # chat never filters by version/variant
    assert len(rer.calls[0][1]) == min(40, context_k)


def test_low_effort_uses_the_identity_reranker_not_the_model():
    rer = RecordingReranker()
    resp = _chat(_orch(reranker=rer), effort=EffortLevel.LOW)

    assert rer.calls == []
    # LOW has context_k=0, so the identity reranker sees no chunks
    assert resp.citations == []


def test_medium_effort_uses_the_configured_reranker():
    rer = RecordingReranker()
    _chat(_orch(reranker=rer), effort=EffortLevel.MEDIUM)

    assert len(rer.calls) == 1


# --- prompt ------------------------------------------------------------------


def test_prompt_contains_context_under_sources_and_the_refusal_sentence():
    gen = RecordingGenerator()
    _chat(_orch(retriever=RecordingRetriever(_chunks(2)), generator=gen))
    prompt = gen.prompts[0]

    assert "(doc0.md)\nDoc text 0." in prompt
    assert "(doc1.md)\nDoc text 1." in prompt
    assert '"The documentation does not cover this."' in prompt
    assert "at most 3 short sentences" in prompt


# --- response ----------------------------------------------------------------


def test_reply_has_citation_markers_stripped():
    gen = RecordingGenerator("Reset the drive [1]. Then restart [2, 3].")
    resp = _chat(_orch(generator=gen))

    assert resp.reply == "Reset the drive. Then restart."


def test_citations_are_the_top_three_reranked_chunks():
    resp = _chat(_orch(retriever=RecordingRetriever(_chunks(6))))

    assert [c.chunk_id for c in resp.citations] == ["c0", "c1", "c2"]
    assert [c.source for c in resp.citations] == ["doc0.md", "doc1.md", "doc2.md"]


def test_no_chunks_still_generates_with_no_citations():
    gen = RecordingGenerator("The documentation does not cover this.")
    resp = _chat(_orch(retriever=RecordingRetriever([]), generator=gen))

    assert resp.reply == "The documentation does not cover this."
    assert resp.citations == []
    assert len(gen.prompts) == 1


def test_turn_is_stored_with_rewritten_query_and_raw_reply():
    pre = RecordingPreprocessor("standalone query")
    gen = RecordingGenerator("Reset it [1].")
    _chat(_orch(pre, generator=gen))

    # current behaviour: the rewrite (not the user's text) is stored, and the reply
    # is stored before citation markers are stripped; alarm is None for chat turns
    assert pre.stored == [("conv-1", "standalone query", "Reset it [1].", None)]


# --- failures ----------------------------------------------------------------


def test_retrieval_failure_raises_retrieval_unavailable():
    pre, gen = RecordingPreprocessor(), RecordingGenerator()
    orch = _orch(pre, RecordingRetriever(error=RuntimeError("db down")), generator=gen)

    with pytest.raises(RetrievalUnavailable):
        _chat(orch)
    assert gen.prompts == []
    assert pre.stored == []


def test_generation_failure_raises_model_unavailable():
    pre = RecordingPreprocessor()
    orch = _orch(pre, generator=RecordingGenerator(error=RuntimeError("ollama down")))

    with pytest.raises(ModelUnavailable):
        _chat(orch)
    assert pre.stored == []
