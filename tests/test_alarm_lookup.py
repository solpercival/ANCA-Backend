"""Alarm catalogue lookup: retrieval runs on the alarm's text; unknown codes 404."""
import asyncio
from contextlib import contextmanager

import pytest

from rag_engine.api.errors import RetrievalUnavailable, UnknownAlarmCode
from rag_engine.api.schemas import ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.orchestrator import Orchestrator, get_orchestrator
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.stores import alarms as alarms_module
from rag_engine.stores.alarms import PostgresAlarmStore
from tests.fakes import FB_0002, FakeAlarmStore


class RecordingRetriever:
    def __init__(self, text="Check the cable."):
        self.queries = []
        self._text = text

    async def retrieve(self, query, top_k, where=None):
        self.queries.append(query)
        return [Chunk(chunk_id="c1", text=self._text, source="m.md", score=0.9)]


class FakeReranker:
    async def rerank(self, query, chunks, top_n):
        return chunks[:top_n]


class FakeGenerator:
    prompt = None

    def __init__(self, answer="Check the cable [1]."):
        self._answer = answer

    async def generate(self, prompt):
        self.prompt = prompt
        return self._answer


class BrokenAlarmStore:
    async def get_alarm(self, code):
        raise ConnectionError("db down")


def _orch(store=None, answer="Check the cable [1]."):
    return Orchestrator(
        RecordingRetriever(), FakeReranker(), FakeGenerator(answer), store or FakeAlarmStore()
    )


def _resolve(answer, code="am.fb.0002"):
    return asyncio.run(_orch(answer=answer).resolve(ResolveRequest(code=code), Tier.technician))


# --- orchestrator ------------------------------------------------------------

def test_retrieves_on_alarm_text_not_code():
    orch = _orch()
    asyncio.run(orch.resolve(ResolveRequest(code="am.fb.0002"), Tier.technician))

    assert orch._retriever.queries == ["EtherCAT slave lost. EtherCAT slave 3 stopped responding."]
    assert "am.fb.0002" not in orch._retriever.queries[0]


def test_free_text_query_takes_precedence():
    orch = _orch()
    asyncio.run(orch.resolve(ResolveRequest(code="am.fb.0002", query="drive trips"), Tier.technician))

    assert orch._retriever.queries == ["drive trips"]


def test_prompt_names_the_alarm():
    orch = _orch()
    asyncio.run(orch.resolve(ResolveRequest(code="am.fb.0002"), Tier.technician))

    assert "am.fb.0002 - EtherCAT slave lost" in orch._generator.prompt


def test_unknown_code_raises_before_retrieval():
    orch = _orch()
    with pytest.raises(UnknownAlarmCode):
        asyncio.run(orch.resolve(ResolveRequest(code="am.fb.9999"), Tier.technician))

    assert orch._retriever.queries == []


def test_catalogue_failure_is_retrieval_unavailable():
    with pytest.raises(RetrievalUnavailable):
        asyncio.run(_orch(BrokenAlarmStore()).resolve(ResolveRequest(code="am.fb.0002"), Tier.technician))


# --- catalogue is header, never guidance ---------------------------------------

def test_response_renders_alarm_header_from_catalogue():
    resp = _resolve("COVERAGE: partial\nCheck the cable [1].")

    assert (resp.title, resp.domain, resp.severity, resp.severity_category) == (
        "EtherCAT slave lost", "Fieldbus", 900, "Error",
    )


def test_prompt_marks_catalogue_text_as_not_documentation():
    orch = _orch()
    asyncio.run(orch.resolve(ResolveRequest(code="am.fb.0002"), Tier.technician))

    assert "not documentation" in orch._generator.prompt
    assert "never repeat it as guidance" in orch._generator.prompt


@pytest.mark.parametrize(
    "echo",
    [
        "EtherCAT slave 3 stopped responding.",  # alarm message verbatim
        "EtherCAT slave 3 stopped responding [1].",  # ...even with a citation marker
        "Ethercat slave 3 has stopped responding.",  # near-verbatim
        "EtherCAT slave lost.",  # title
    ],
)
def test_step_restating_catalogue_text_is_dropped(echo):
    resp = _resolve(f"COVERAGE: partial\n{echo}\nCheck the cable [1].")

    assert resp.steps == ["Check the cable."]


def test_echo_is_kept_when_the_docs_say_the_same():
    # the docs themselves state it, so it is doc guidance that happens to match the alarm
    orch = Orchestrator(
        RecordingRetriever("If a slave dies, EtherCAT slave 3 stopped responding is reported."),
        FakeReranker(),
        FakeGenerator("COVERAGE: partial\nEtherCAT slave 3 stopped responding [1]."),
        FakeAlarmStore(),
    )
    resp = asyncio.run(orch.resolve(ResolveRequest(code="am.fb.0002"), Tier.technician))

    assert resp.steps == ["EtherCAT slave 3 stopped responding."]


def test_explanation_that_mentions_the_alarm_is_kept():
    step = "Slave 3 stopped responding because its EtherCAT state no longer matches the master."
    resp = _resolve(f"COVERAGE: partial\n{step}")

    assert resp.steps == [step]


def test_answer_of_only_catalogue_echoes_is_coverage_none():
    resp = _resolve("COVERAGE: full\nEtherCAT slave 3 stopped responding.")

    assert resp.doc_coverage == "none"
    assert resp.steps == ["The documentation does not cover this alarm."]
    assert resp.likely_causes == []


def test_catalogue_text_cannot_become_a_likely_cause():
    # the alarm message is in the prompt but not in the retrieved context
    resp = _resolve("COVERAGE: partial\nCheck the cable [1].\nCAUSE: EtherCAT slave 3 stopped responding.")

    assert resp.likely_causes == []


# --- seed ----------------------------------------------------------------------

def test_seed_source_is_the_sample_catalogue():
    # populate_alarms (the DB upsert) is covered by test_ingestion against Postgres
    from ingestion.seed_alarms import load_alarms

    data = load_alarms()

    codes = [a["code"] for a in data["alarms"]]
    assert len(codes) == 11
    assert "am.fb.0002" in codes
    assert "fb" in data["_modules"]
    assert all({"title", "alarm_text", "severity", "severity_category"} <= a.keys() for a in data["alarms"])


# --- API ---------------------------------------------------------------------

def test_api_unknown_code_returns_404_envelope(client, bearer):
    r = client.post("/api/v2/resolve", json={"code": "am.fb.9999"}, headers=bearer)

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "unknown_alarm_code"


def test_api_catalogue_down_returns_503(client, bearer):
    from rag_engine.main import app

    app.dependency_overrides[get_orchestrator] = lambda: _orch(BrokenAlarmStore())
    r = client.post("/api/v2/resolve", json={"code": "am.fb.0002"}, headers=bearer)

    assert r.status_code == 503
    assert r.json()["error"]["code"] == "retrieval_unavailable"


# --- PostgresAlarmStore --------------------------------------------------------

class FakeConn:
    def __init__(self, row):
        self.row = row
        self.params = None

    def execute(self, sql, params):
        self.params = params
        return self

    def fetchone(self):
        return self.row


def _patch_conn(monkeypatch, row):
    conn = FakeConn(row)

    @contextmanager
    def fake_get_db_conn():
        yield conn

    monkeypatch.setattr(alarms_module, "get_db_conn", fake_get_db_conn)
    return conn


def test_store_maps_row_to_alarm(monkeypatch):
    conn = _patch_conn(monkeypatch, {
        "title": FB_0002.title, "domain": "Fieldbus", "severity_score": 900,
        "severity_category": "error", "alarm_text": FB_0002.alarm_text, "data_fields": {"slave": 3},
    })

    alarm = asyncio.run(PostgresAlarmStore().get_alarm("am.fb.0002"))

    assert conn.params == ("am", "fb", "0002")
    assert alarm.code == "am.fb.0002"
    assert alarm.title == FB_0002.title
    assert alarm.data_fields == {"slave": 3}


def test_store_returns_none_for_missing_row(monkeypatch):
    _patch_conn(monkeypatch, None)

    assert asyncio.run(PostgresAlarmStore().get_alarm("am.fb.9999")) is None


def test_store_rejects_malformed_code_without_querying(monkeypatch):
    conn = _patch_conn(monkeypatch, None)

    assert asyncio.run(PostgresAlarmStore().get_alarm("am.fb")) is None
    assert conn.params is None
