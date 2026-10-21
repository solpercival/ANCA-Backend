"""Tiered documentation access: operators may only draw on the Part Programmer's
Reference; technicians and partners on all docs. Covers the tier rule (auth/tiers.py),
its path through Orchestrator -> HybridRetriever -> the stores on both the resolve
and chat paths, and the SQL predicate the Postgres searches add. No services needed.
"""

import asyncio
from contextlib import contextmanager

import pytest

from rag_engine.api.schemas import ChatRequest, ResolveRequest
from rag_engine.auth.tiers import DocAudience, Tier, allowed_doc_audiences
from rag_engine.config import get_settings
from rag_engine.orchestrator import Orchestrator
from rag_engine.retrieval.doc_refs import doc_path
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.stores import search
from rag_engine.stores.search import PostgresDBConnection
from tests.fakes import (
    PPR_DOC,
    USER_GUIDE_DOC,
    FakeAlarmStore,
    FakeDocStore,
    FakeEmbedder,
    FakePreprocessor,
)

USER_GUIDE = Chunk(chunk_id="ug1", text="Reset the CoE device from the HMI.", source=USER_GUIDE_DOC)
PPR = Chunk(chunk_id="ppr1", text="Restart the part program.", source=PPR_DOC)
OPERATOR_WHERE = {"doc_audiences": [DocAudience.part_programmers_reference]}


class FakeReranker:
    async def rerank(self, query, chunks, effort):
        return chunks[: effort.reranker_n]


class ContextGenerator:
    """Answers with a step when the prompt has any document context, else claims
    no coverage -- like a grounded model with nothing to go on."""

    async def generate(self, prompt, tokens=None, thinking=False, deterministic=False):
        if "(user-guide/" in prompt or "(part-programmers-reference/" in prompt:
            return "COVERAGE: full\nReset the device."
        return "COVERAGE: none\n"


@pytest.fixture(params=["unified", "dual"])
def embedding_setup(request, monkeypatch):
    monkeypatch.setattr(get_settings(), "embedding_setup", request.param)
    return request.param


def _orch(store):
    retriever = HybridRetriever(FakeEmbedder(), FakeEmbedder(), store, store)
    return Orchestrator(
        FakePreprocessor(), retriever, FakeReranker(), ContextGenerator(), FakeAlarmStore()
    )


def _resolve(store, tier):
    return asyncio.run(_orch(store).resolve(ResolveRequest(code="am.fb.0002"), tier))


def _chat(store, tier):
    req = ChatRequest(conversation_id="conv-1", message="how do I reset the device?")
    return asyncio.run(_orch(store).chat(req, tier))


def _sources(resp):
    return {c.path for c in resp.citations}


# --- the tier rule -----------------------------------------------------------


def test_operator_may_only_use_the_part_programmers_reference():
    assert allowed_doc_audiences(Tier.operator) == {DocAudience.part_programmers_reference}


@pytest.mark.parametrize("tier", [Tier.technician, Tier.partner])
def test_technician_and_partner_are_unrestricted(tier):
    assert allowed_doc_audiences(tier) is None


def test_every_tier_has_a_rule():
    for tier in Tier:
        allowed_doc_audiences(tier)  # KeyError if a new tier is added without one


def test_audience_fragments_match_the_doc_folders():
    assert DocAudience.user_guide.path_fragment in USER_GUIDE_DOC
    assert DocAudience.part_programmers_reference.path_fragment in PPR_DOC
    assert DocAudience.user_guide.path_fragment not in PPR_DOC


# --- resolve -----------------------------------------------------------------


def test_operator_resolve_excludes_user_guide_sources(embedding_setup):
    store = FakeDocStore(USER_GUIDE, PPR)
    resp = _resolve(store, Tier.operator)

    assert _sources(resp) == {doc_path(PPR_DOC)}
    # every search (semantic, plus lexical in dual mode) got the restriction
    kinds = ["semantic"] if embedding_setup == "unified" else ["semantic", "lexical"]
    assert store.calls == [(k, OPERATOR_WHERE) for k in kinds]


def test_operator_resolve_with_only_user_guide_coverage_falls_to_none():
    resp = _resolve(FakeDocStore(USER_GUIDE), Tier.operator)

    assert resp.citations == []
    assert resp.doc_coverage == "none"


@pytest.mark.parametrize("tier", [Tier.technician, Tier.partner])
def test_technician_and_partner_resolve_include_user_guide(tier):
    store = FakeDocStore(USER_GUIDE, PPR)
    resp = _resolve(store, tier)

    assert _sources(resp) == {doc_path(USER_GUIDE_DOC), doc_path(PPR_DOC)}
    assert store.calls[0] == ("semantic", None)  # unchanged: no filter at all


def test_operator_restriction_combines_with_env_filters():
    store = FakeDocStore(PPR)
    req = ResolveRequest(code="am.fb.0002", env={"machine_variant": "TX7"})
    asyncio.run(_orch(store).resolve(req, Tier.operator))

    assert store.calls[0][1] == {**OPERATOR_WHERE, "machine_variant": "TX7"}


# --- chat --------------------------------------------------------------------


def test_operator_chat_excludes_user_guide_sources():
    # the route refuses operator chat; the orchestrator still applies the rule
    store = FakeDocStore(USER_GUIDE, PPR)
    resp = _chat(store, Tier.operator)

    assert _sources(resp) == {doc_path(PPR_DOC)}
    assert store.calls[0] == ("semantic", OPERATOR_WHERE)


@pytest.mark.parametrize("tier", [Tier.technician, Tier.partner])
def test_technician_and_partner_chat_include_user_guide(tier):
    store = FakeDocStore(USER_GUIDE, PPR)
    resp = _chat(store, tier)

    assert _sources(resp) == {doc_path(USER_GUIDE_DOC), doc_path(PPR_DOC)}
    assert store.calls[0] == ("semantic", None)


# --- Postgres SQL ------------------------------------------------------------


class RecordingConn:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((sql, params))
        return self

    def fetchall(self):
        return []


@pytest.fixture
def conn(monkeypatch):
    recording = RecordingConn()

    @contextmanager
    def fake_db_conn():
        yield recording

    monkeypatch.setattr(search, "get_db_conn", fake_db_conn)
    return recording


SEARCHES = [
    lambda db, where: db._semantic_search_sync([0.1, 0.2], 5, where),
    lambda db, where: db._lexical_search_sync({1: 0.5}, 5, where),
]


@pytest.mark.parametrize("run", SEARCHES, ids=["semantic", "lexical"])
def test_sql_restricts_operator_to_part_programmers_reference(conn, run):
    run(PostgresDBConnection(), OPERATOR_WHERE)
    sql, params = conn.executed[0]

    assert "document_source LIKE ANY(%s)" in sql
    assert ["%/part-programmers-reference/%"] in params
    assert sql.count("%s") == len(params)


@pytest.mark.parametrize("run", SEARCHES, ids=["semantic", "lexical"])
@pytest.mark.parametrize("where", [None, {}, {"machine_variant": "TX7"}])
def test_sql_has_no_document_filter_without_doc_audiences(conn, run, where):
    run(PostgresDBConnection(), where)
    sql, params = conn.executed[0]

    assert "document_source LIKE" not in sql
    assert sql.count("%s") == len(params)


@pytest.mark.parametrize("run", SEARCHES, ids=["semantic", "lexical"])
def test_sql_combines_audience_with_env_filters(conn, run):
    run(PostgresDBConnection(), {**OPERATOR_WHERE, "machine_variant": "TX7"})
    sql, params = conn.executed[0]

    assert "metadata->>'machine_variant' = %s" in sql
    assert "document_source LIKE ANY(%s)" in sql
    assert sql.count("%s") == len(params)
