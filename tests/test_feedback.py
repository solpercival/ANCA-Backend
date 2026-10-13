"""POST <API_PREFIX>/feedback ("this did not help"): the route, the Postgres
write, and the rewriter seeing the feedback on the conversation's next turn.

The route tests run a real QueryPreprocessor over an in-memory chat store, so
/chat -> /feedback -> /chat goes through the same store the rewriter reads.
No Postgres, Redis or model server is needed.
"""

from contextlib import contextmanager

import pytest

from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.config import API_PREFIX, get_settings
from rag_engine.main import app
from rag_engine.orchestrator import Orchestrator, get_orchestrator
from rag_engine.retrieval.hybrid import HybridRetriever
from rag_engine.retrieval.rewriter import QueryPreprocessor
from rag_engine.stores import search
from rag_engine.stores.search import PostgresDBConnection
from tests.conftest import (
    FakeDenseEmbedder,
    FakeGenerator,
    FakeLexical,
    FakeReranker,
    FakeSparseEmbedder,
    FakeVectorStore,
)
from tests.fakes import FakeAlarmStore

CONV = "conv-feedback"


class InMemoryChatStore:
    """ChatStore with the same semantics as the Postgres one: ids are assigned on
    insert, and feedback only lands on a turn in the given conversation."""

    def __init__(self):
        self.rows: list[dict] = []

    def store_query_result(self, conversation_id, query, response, alarm_str):
        response_id = len(self.rows) + 1
        self.rows.append(
            {
                "response_id": response_id,
                "conversation_id": conversation_id,
                "query": query,
                "response": response,
                "user_feedback": None,
            }
        )
        return response_id

    async def context_search(self, conversation_id):
        context = []
        for row in self.rows:
            if row["conversation_id"] == conversation_id:
                context.append((row["query"], None))
                context.append((row["response"], row["user_feedback"]))
        return context

    async def set_feedback(self, conversation_id, response_id, helpful):
        for row in self.rows:
            if row["response_id"] == response_id and row["conversation_id"] == conversation_id:
                row["user_feedback"] = helpful
                return True
        return False


class FakeKeywordStore:
    async def keyword_search(self, query, top_k):
        return ["EtherCAT"]


class RecordingRewriteModel:
    """Rewrite model that records each prompt it is given."""

    def __init__(self):
        self.prompts: list[str] = []

    async def generate(self, prompt, tokens=None, thinking=False):
        self.prompts.append(prompt)
        return "rewritten query"


@pytest.fixture
def chat_store():
    return InMemoryChatStore()


@pytest.fixture
def rewrite_model():
    return RecordingRewriteModel()


@pytest.fixture
def feedback_client(client, chat_store, rewrite_model):
    """The conftest client, but with one orchestrator (shared across requests) whose
    preprocessor is real and backed by chat_store."""
    retriever = HybridRetriever(
        FakeDenseEmbedder(), FakeSparseEmbedder(), FakeVectorStore(), FakeLexical()
    )
    preprocessor = QueryPreprocessor(chat_store, FakeKeywordStore(), rewrite_model, keywd_k=1)
    orch = Orchestrator(preprocessor, retriever, FakeReranker(), FakeGenerator(), FakeAlarmStore())
    app.dependency_overrides[get_orchestrator] = lambda: orch
    return client


def _chat(client, headers, message):
    r = client.post(
        f"{API_PREFIX}/chat",
        json={"conversation_id": CONV, "message": message},
        headers=headers,
    )
    assert r.status_code == 200
    return r.json()


def _feedback(client, headers, response_id, helpful, conversation_id=CONV):
    return client.post(
        f"{API_PREFIX}/feedback",
        json={"conversation_id": conversation_id, "response_id": response_id, "helpful": helpful},
        headers=headers,
    )


# write path


def test_chat_returns_response_id(feedback_client, bearer, chat_store):
    body = _chat(feedback_client, bearer, "How do I reset the EtherCAT drive?")

    assert body["response_id"] == chat_store.rows[0]["response_id"]


def test_feedback_writes_user_feedback(feedback_client, bearer, chat_store):
    response_id = _chat(feedback_client, bearer, "How do I reset the EtherCAT drive?")[
        "response_id"
    ]

    r = _feedback(feedback_client, bearer, response_id, helpful=False)

    assert r.status_code == 204
    assert r.content == b""
    assert chat_store.rows[0]["user_feedback"] is False


def test_feedback_can_be_changed(feedback_client, bearer, chat_store):
    response_id = _chat(feedback_client, bearer, "How do I reset the EtherCAT drive?")[
        "response_id"
    ]

    assert _feedback(feedback_client, bearer, response_id, helpful=False).status_code == 204
    assert _feedback(feedback_client, bearer, response_id, helpful=True).status_code == 204
    assert chat_store.rows[0]["user_feedback"] is True


def test_unknown_response_is_not_found(feedback_client, bearer):
    r = _feedback(feedback_client, bearer, response_id=999, helpful=False)

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_response_from_another_conversation_is_not_found(feedback_client, bearer, chat_store):
    response_id = _chat(feedback_client, bearer, "How do I reset the EtherCAT drive?")[
        "response_id"
    ]

    r = _feedback(feedback_client, bearer, response_id, False, conversation_id="someone-else")

    assert r.status_code == 404
    assert chat_store.rows[0]["user_feedback"] is None


@pytest.mark.parametrize(
    "body",
    [
        {"conversation_id": CONV, "response_id": 1},  # no helpful
        {"conversation_id": CONV, "helpful": False},  # no response_id
        {"response_id": 1, "helpful": False},  # no conversation_id
        {"conversation_id": CONV, "response_id": 0, "helpful": False},
        {"conversation_id": "", "response_id": 1, "helpful": False},
    ],
)
def test_invalid_body_is_a_validation_error(feedback_client, bearer, body):
    r = feedback_client.post(f"{API_PREFIX}/feedback", json=body, headers=bearer)

    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


# auth and rate limiting


def test_feedback_requires_a_token(feedback_client):
    r = feedback_client.post(
        f"{API_PREFIX}/feedback",
        json={"conversation_id": CONV, "response_id": 1, "helpful": False},
    )

    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


@pytest.mark.parametrize(
    "tier, expected", [(Tier.operator, 403), (Tier.technician, 204), (Tier.partner, 204)]
)
def test_feedback_follows_chat_tier_access(feedback_client, chat_store, tier, expected):
    response_id = chat_store.store_query_result(CONV, "q", "a", None)
    token, _ = create_access_token(user_id=1, tier=tier)

    r = _feedback(feedback_client, {"Authorization": f"Bearer {token}"}, response_id, helpful=False)

    assert r.status_code == expected


def test_feedback_is_rate_limited_in_its_own_bucket(
    feedback_client, bearer, chat_store, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(settings, "feedback_rate_limit_per_ip", 1)
    monkeypatch.setattr(settings, "feedback_rate_limit_per_tier", 100)
    monkeypatch.setattr(settings, "chat_rate_limit_per_ip", 1)
    monkeypatch.setattr(settings, "chat_rate_limit_per_tier", 100)

    # the chat request uses up the chat bucket, not the feedback one
    response_id = _chat(feedback_client, bearer, "How do I reset the EtherCAT drive?")[
        "response_id"
    ]
    first = _feedback(feedback_client, bearer, response_id, helpful=False)
    second = _feedback(feedback_client, bearer, response_id, helpful=True)

    assert first.status_code == 204
    assert second.status_code == 429
    assert int(second.headers["retry-after"]) > 0
    assert second.json()["error"]["code"] == "rate_limited"
    assert chat_store.rows[0]["user_feedback"] is False


# the rewriter on the next turn


def _context_section(prompt: str) -> str:
    """The prompt's <context> section. The rewrite instructions also mention
    <context> (and both status tags), so take the last occurrence."""
    start = prompt.rindex("<context>")
    return prompt[start : prompt.index("</context>", start)]


def test_rewriter_sees_failed_status_on_next_turn(feedback_client, bearer, rewrite_model):
    response_id = _chat(feedback_client, bearer, "How do I reset the EtherCAT drive?")[
        "response_id"
    ]
    assert rewrite_model.prompts == []  # no history yet, so no rewrite

    assert _feedback(feedback_client, bearer, response_id, helpful=False).status_code == 204
    # a pronoun makes the follow-up depend on context, so the rewrite runs
    _chat(feedback_client, bearer, "it still faults after that")

    assert len(rewrite_model.prompts) == 1
    context = _context_section(rewrite_model.prompts[0])
    assert "[assist]:" in context
    assert context.rstrip().endswith("[status: failed]")
    assert "[status: success]" not in context


def test_rewriter_sees_success_status_on_next_turn(feedback_client, bearer, rewrite_model):
    response_id = _chat(feedback_client, bearer, "How do I reset the EtherCAT drive?")[
        "response_id"
    ]

    assert _feedback(feedback_client, bearer, response_id, helpful=True).status_code == 204
    _chat(feedback_client, bearer, "it still faults after that")

    context = _context_section(rewrite_model.prompts[0])
    assert context.rstrip().endswith("[status: success]")


def test_rewriter_shows_no_status_without_feedback(feedback_client, bearer, rewrite_model):
    _chat(feedback_client, bearer, "How do I reset the EtherCAT drive?")
    _chat(feedback_client, bearer, "it still faults after that")

    assert "[status:" not in _context_section(rewrite_model.prompts[0])


# Postgres store: the SQL the write path sends


class _RecordingConn:
    def __init__(self, row):
        self.row = row
        self.executed: list[tuple[str, list]] = []
        self.committed = False

    def execute(self, sql, params):
        self.executed.append((sql, params))
        return self

    def fetchone(self):
        return self.row

    def commit(self):
        self.committed = True


def _patch_db(monkeypatch, conn):
    @contextmanager
    def fake_get_db_conn():
        yield conn

    monkeypatch.setattr(search, "get_db_conn", fake_get_db_conn)


@pytest.mark.parametrize("row, updated", [({"response_id": 7}, True), (None, False)])
async def test_postgres_set_feedback(monkeypatch, row, updated):
    conn = _RecordingConn(row)
    _patch_db(monkeypatch, conn)

    assert await PostgresDBConnection().set_feedback(CONV, 7, False) is updated

    ((sql, params),) = conn.executed
    assert "UPDATE response SET user_feedback" in sql
    assert "response_id = %s AND conversation_id = %s" in sql
    assert params == [False, 7, CONV]
    assert conn.committed


def test_postgres_store_query_result_returns_response_id(monkeypatch):
    conn = _RecordingConn({"response_id": 42})
    _patch_db(monkeypatch, conn)

    assert PostgresDBConnection().store_query_result(CONV, "q", "a", None) == 42
    assert "RETURNING response_id" in conn.executed[0][0]
