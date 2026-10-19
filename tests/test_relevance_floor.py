"""Relevance floor on resolve (RESOLVE_MIN_RELEVANCE): when even the best reranked
chunk is irrelevant, the answer is "not covered" and the generator is not called,
so it cannot build steps out of unrelated text. Found on the integration bench: an
operator asking about a User Guide-only alarm got steps from unrelated Part
Programmer's Reference pages (best score 0.02). No services needed."""

import asyncio

import pytest

from rag_engine.api.schemas import EffortLevel, ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.config import get_settings
from rag_engine.orchestrator import _NOT_COVERED, Orchestrator
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker
from tests.fakes import FakeAlarmStore, FakePreprocessor

CAUSE = "The fault is caused by a loose EtherCAT cable."


class Retriever:
    def __init__(self, n=3):
        self._n = n

    async def retrieve(self, query, top_k, where=None):
        return [
            Chunk(chunk_id=str(i), text=f"Reset the drive. {CAUSE}", source=f"doc{i}.md")
            for i in range(self._n)
        ]


class ScoringReranker:
    """Stands in for Qwen3: sets chunk.score to a relevance probability."""

    scores_relevance = True

    def __init__(self, *scores):
        self._scores = scores

    async def rerank(self, query, chunks, effort):
        for chunk, score in zip(chunks, self._scores, strict=False):
            chunk.score = score
        return sorted(chunks, key=lambda c: c.score, reverse=True)[: effort.reranker_n]


class UnscoredReranker:
    """Like the fakes elsewhere and IdentityReranker: scores carry no meaning."""

    async def rerank(self, query, chunks, effort):
        return chunks[: effort.reranker_n]


class Generator:
    def __init__(self, answer=f"COVERAGE: partial\nReset the drive.\nCAUSE: {CAUSE}"):
        self._answer = answer
        self.calls = 0

    async def generate(self, prompt, tokens=None, thinking=False, deterministic=False):
        self.calls += 1
        return self._answer


def _resolve(reranker, generator=None, retriever=None, effort=EffortLevel.MEDIUM):
    generator = generator or Generator()
    orch = Orchestrator(
        FakePreprocessor(), retriever or Retriever(), reranker, generator, FakeAlarmStore()
    )
    req = ResolveRequest(code="am.fb.0002", effort=effort)
    return asyncio.run(orch.resolve(req, Tier.technician)), generator


def test_default_floor():
    assert get_settings().resolve_min_relevance == 0.1


@pytest.mark.parametrize("scores", [(0.02, 0.01, 0.01), (0.0, 0.0, 0.0), (0.09, 0.05, 0.0)])
def test_irrelevant_context_is_not_covered_without_calling_the_model(scores):
    resp, generator = _resolve(ScoringReranker(*scores))

    assert generator.calls == 0
    assert resp.doc_coverage == "none"
    assert resp.confidence == 0.0
    assert resp.steps == [_NOT_COVERED]
    assert resp.likely_causes == []
    assert resp.citations == []
    # the alarm header still identifies the alarm
    assert resp.title == "EtherCAT slave lost"


@pytest.mark.parametrize("scores", [(0.1, 0.0, 0.0), (0.47, 0.08, 0.06), (0.93, 0.07, 0.04)])
def test_one_relevant_chunk_is_enough_to_answer(scores):
    # only the best score counts: am.nc.0004's answer rests on one chunk at 0.93
    resp, generator = _resolve(ScoringReranker(*scores))

    assert generator.calls == 1
    assert resp.doc_coverage == "partial"
    assert resp.steps == ["Reset the drive."]
    assert resp.likely_causes == [CAUSE]
    assert len(resp.citations) == 3


def test_no_chunks_at_all_is_not_covered():
    resp, generator = _resolve(ScoringReranker(), retriever=Retriever(n=0))

    assert generator.calls == 0
    assert resp.doc_coverage == "none"


@pytest.mark.parametrize("reranker", [UnscoredReranker(), IdentityReranker()])
def test_floor_is_ignored_when_the_reranker_does_not_score_relevance(reranker):
    # chunk.score is 0 here, but it is not a relevance probability
    resp, generator = _resolve(reranker)

    assert generator.calls == 1
    assert resp.doc_coverage == "partial"


def test_low_effort_uses_the_identity_reranker_so_the_floor_does_not_apply():
    resp, generator = _resolve(ScoringReranker(0.0, 0.0, 0.0), effort=EffortLevel.LOW)

    assert generator.calls == 1


def test_floor_can_be_disabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "resolve_min_relevance", 0.0)

    resp, generator = _resolve(ScoringReranker(0.0, 0.0, 0.0))

    assert generator.calls == 1


def test_floor_is_configurable(monkeypatch):
    monkeypatch.setattr(get_settings(), "resolve_min_relevance", 0.5)

    resp, generator = _resolve(ScoringReranker(0.47, 0.08, 0.06))

    assert generator.calls == 0
    assert resp.doc_coverage == "none"


def test_answer_the_model_calls_not_covered_has_no_citations():
    # relevant-looking chunks, but the model found nothing in them for this alarm
    generator = Generator(f"COVERAGE: none\n{_NOT_COVERED}")
    resp, _ = _resolve(ScoringReranker(0.9, 0.5, 0.2), generator)

    assert generator.calls == 1
    assert resp.doc_coverage == "none"
    assert resp.citations == []


def test_real_rerankers_declare_whether_they_score_relevance():
    assert Qwen3Reranker.scores_relevance is True
    assert IdentityReranker.scores_relevance is False
