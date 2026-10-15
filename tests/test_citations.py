"""Citations in the contract's {doc, path, section} shape: the source -> doc/path
mapping (retrieval/doc_refs.py), the heading the Postgres searches return as
Chunk.section, and the citations resolve and chat build from the top chunks.
No services needed."""

import asyncio
import json
from contextlib import contextmanager
from pathlib import Path

import pytest
from eval.run_eval import GOLD_PATH, score_code

from rag_engine.api.schemas import ChatRequest, Citation, ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.orchestrator import Orchestrator
from rag_engine.retrieval.doc_refs import DOC_NAMES, DOCS_ROOT, UNKNOWN_DOC, doc_name, doc_path
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.stores import search
from rag_engine.stores.search import PostgresDBConnection
from tests.fakes import FakeAlarmStore, FakePreprocessor

PPR = "part-programmers-reference/05-functions.md"
GUIDE = "user-guide/troubleshoot/coe-device-errors.md"


# --- source -> path / doc ----------------------------------------------------


@pytest.mark.parametrize(
    ("source", "path"),
    [
        (f"{DOCS_ROOT}{PPR}", PPR),  # as ingestion stores it
        (f"{DOCS_ROOT}{GUIDE}", GUIDE),
        (f"/app/{DOCS_ROOT}{GUIDE}", GUIDE),  # absolute, in a container
        (f"C:\\repo\\docs\\docs-proto\\starter-kit\\docs\\{PPR}".replace("/", "\\"), PPR),
        (f"/srv/manuals/{GUIDE}", GUIDE),  # another root: cut at the document folder
        (PPR, PPR),  # already relative
        ("manual.md", "manual.md"),
        ("/tmp/notes/manual.md", "tmp/notes/manual.md"),  # unknown root: only the slash goes
    ],
)
def test_doc_path_is_relative_to_the_docs_root(source, path):
    assert doc_path(source) == path


@pytest.mark.parametrize(
    ("path", "doc"),
    [
        (PPR, "Part Programmer's Reference"),
        (GUIDE, "AMCore User Guide"),
        ("release-notes/v2.md", "Release Notes"),  # unnamed folder: its name, title-cased
        ("manual.md", UNKNOWN_DOC),
    ],
)
def test_doc_name_comes_from_the_top_level_folder(path, doc):
    assert doc_name(path) == doc


def test_doc_names_match_the_reference_answers():
    # the display names are the ones the starter kit's gold answers use
    if not Path(GOLD_PATH).exists():
        pytest.skip("docs submodule not checked out")
    answers = json.loads(Path(GOLD_PATH).read_text(encoding="utf-8"))["answers"]
    refs = [ref for answer in answers.values() for ref in answer["doc_refs"]]

    assert {(ref["path"].split("/")[0], ref["doc"]) for ref in refs} == set(DOC_NAMES.items())


# --- citations built by the orchestrator -------------------------------------


def _chunk(i, path=PPR, section="spline"):
    return Chunk(chunk_id=str(i), text=f"text {i}", source=f"{DOCS_ROOT}{path}", section=section)


def test_citation_has_doc_path_and_section_only():
    (citation,) = Orchestrator._citations([_chunk(13410, GUIDE, "Emergency Error")])

    assert citation.model_dump() == {
        "doc": "AMCore User Guide",
        "path": GUIDE,
        "section": "Emergency Error",
    }


def test_citation_has_no_local_prefix_or_chunk_number():
    dumped = json.dumps([c.model_dump() for c in Orchestrator._citations([_chunk(13410)])])

    assert "docs-proto" not in dumped
    assert "starter-kit" not in dumped
    assert "13410" not in dumped
    assert "chunk_id" not in dumped


@pytest.mark.parametrize(
    ("heading", "section"),
    [
        ("`G60` — `splineon`", "G60 — splineon"),  # live am.nc.0004 heading
        ("electronic_cam", "electronic_cam"),  # underscores are part of the name
        ("Example  Configurations:", "Example Configurations:"),
    ],
)
def test_section_is_the_heading_without_inline_code_marks(heading, section):
    (citation,) = Orchestrator._citations([_chunk(1, section=heading)])

    assert citation.section == section


@pytest.mark.parametrize("heading", [None, "", "``"])
def test_chunk_without_a_heading_has_null_section(heading):
    (citation,) = Orchestrator._citations([_chunk(1, section=heading)])

    assert citation.section is None


def test_chunks_of_the_same_section_are_one_citation():
    chunks = [_chunk(1), _chunk(2), _chunk(3, section="electronic_cam")]

    assert [c.section for c in Orchestrator._citations(chunks)] == ["spline", "electronic_cam"]


def test_only_the_top_three_chunks_are_cited():
    chunks = [_chunk(i, section=f"s{i}") for i in range(5)]

    assert [c.section for c in Orchestrator._citations(chunks)] == ["s0", "s1", "s2"]


def test_am_nc_0004_citations_match_its_reference_doc_refs():
    # retrieving the gold chunks must produce exactly the gold doc_refs
    if not Path(GOLD_PATH).exists():
        pytest.skip("docs submodule not checked out")
    answers = json.loads(Path(GOLD_PATH).read_text(encoding="utf-8"))["answers"]
    doc_refs = answers["am.nc.0004"]["doc_refs"]
    chunks = [_chunk(i, ref["path"], ref["section"]) for i, ref in enumerate(doc_refs)]

    assert [c.model_dump() for c in Orchestrator._citations(chunks)] == doc_refs


class FakeRetriever:
    async def retrieve(self, query, top_k, where=None):
        return [_chunk(1, PPR, "spline"), _chunk(2, GUIDE, None)]


class FakeReranker:
    async def rerank(self, query, chunks, effort):
        return chunks[: effort.reranker_n]


class FakeGenerator:
    async def generate(self, prompt, tokens=None, thinking=False):
        return "COVERAGE: partial\nCheck the spline control points."


EXPECTED = [
    Citation(doc="Part Programmer's Reference", path=PPR, section="spline"),
    Citation(doc="AMCore User Guide", path=GUIDE, section=None),
]


def _orch():
    return Orchestrator(
        FakePreprocessor(), FakeRetriever(), FakeReranker(), FakeGenerator(), FakeAlarmStore()
    )


def test_resolve_returns_contract_citations():
    resp = asyncio.run(_orch().resolve(ResolveRequest(code="am.fb.0002"), Tier.technician))

    assert resp.citations == EXPECTED


def test_chat_returns_contract_citations():
    req = ChatRequest(conversation_id="c-1", message="how many control points does a spline need?")
    resp = asyncio.run(_orch().chat(req, Tier.technician))

    assert resp.citations == EXPECTED


def test_eval_scores_retrieval_on_the_citation_path():
    gold = {"doc_refs": [{"doc": "x", "path": PPR, "section": "spline"}]}
    citations = [c.model_dump() for c in EXPECTED]  # PPR first, then the user guide

    scores = score_code(citations, gold)

    assert (scores["hit"], scores["precision"], scores["recall"]) == (True, 0.5, 1.0)
    assert scores["reciprocal_rank"] == 1.0


# --- the stores return the heading -------------------------------------------


class RecordingConn:
    """Returns one row with a heading and one without."""

    def __init__(self):
        self.sql = None

    def execute(self, sql, params):
        self.sql = sql
        return self

    def fetchall(self):
        row = {"content": "t", "metadata": {}, "file_path": f"{DOCS_ROOT}{PPR}"}
        return [
            {**row, "chunk_id": 1, "section": "spline"},
            {**row, "chunk_id": 2, "section": None},
        ]


@pytest.fixture
def conn(monkeypatch):
    recording = RecordingConn()

    @contextmanager
    def fake_db_conn():
        yield recording

    monkeypatch.setattr(search, "get_db_conn", fake_db_conn)
    return recording


SEARCHES = [
    lambda db: db._semantic_search_sync([0.1, 0.2], 5, None),
    lambda db: db._lexical_search_sync({1: 0.5}, 5, None),
]


@pytest.mark.parametrize("run", SEARCHES, ids=["semantic", "lexical"])
def test_search_selects_the_closest_heading_as_section(conn, run):
    chunks = run(PostgresDBConnection())
    sql = " ".join(conn.sql.split())

    assert "SELECT h.heading_order FROM heading h" in sql
    assert "WHERE h.heading_id = document_chunks.closest_heading ) AS section" in sql
    assert [(c.chunk_id, c.section) for c in chunks] == [("1", "spline"), ("2", None)]
