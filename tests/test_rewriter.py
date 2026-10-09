"""Query preprocessing (retrieval/rewriter.py): normalisation, when a rewrite
is needed, and how conversation context is formatted for the rewrite prompt.
"""
import pytest
from rag_engine.retrieval.rewriter import Query, QueryPreprocessor
from rag_engine.stores.search import PostgresDBConnection
from rag_engine.config import get_settings

@pytest.fixture(scope="module")
def preprocessor():
    return QueryPreprocessor(
        chat_db=None,
        keyword_db=None,
        rewrite_model=None,
        keywd_k=5
    )

# Query class initialization tests
def test_query_initialization():
    context = ["user: hello", "assist: hi there"]
    query = Query("what is this?", context)
    
    assert query.resolved_query == "what is this?"
    assert query.context == context
    
def test_query_empty_context():
    query = Query("test query", [])
    assert query.context == []

# _normalize_query() tests
def test_normalize_basic(preprocessor):
    assert preprocessor._normalize_query("HELLO WORLD   ") == "hello world"

def test_normalize_remove_conversational_filler(preprocessor):
    result = preprocessor._normalize_query("can you help me resolve the issue with this alarm?")
    assert "can" not in result.lower() or "like" not in result.lower()
    assert len("can you help me resolve the issue with this alarm?") > len(result)

def test_normalize_punctuation_remove(preprocessor):
    result = preprocessor._normalize_query("I don't understand this. What is this referring to?")
    assert "?" not in result

def test_normalize_combined(preprocessor):
    result = preprocessor._normalize_query("  HELLO World!?  ")
    assert result == "hello world"

# Query class tests
def test_create_query_basic(preprocessor):
    context = ["user: hi"]
    query = preprocessor._create_query("test query", context)
    
    assert isinstance(query, Query)
    assert query.resolved_query == "test query"
    assert query.context == context

# _process_context() tests
def test_process_context_empty(preprocessor):
    result = preprocessor._process_context([], prev_k=3)
    assert result == ""

def test_process_context_basic(preprocessor):
    fake_context = [("user-query-1", None), ("assistant-response-1", None), ("user-query-2", None), ("assistant-response-2", None), ("user-query-3", None), ("assistant-response-3", None)]
    result = preprocessor._process_context(fake_context, 3)

    assert (len(result.split("\n")) == 3)
    assert "<context>" in result
    assert "</context>" in result

    result = result.replace("<context>", "")
    result = result.replace("</context>", "")
    result = result.split("\n")

    assert all(result[i] == fake_context[i] for i in range(-3,0,-1))

def test_process_context_status(preprocessor):
    fake_context = [("user-query-1", None), ("assistant-response-1", True), ("user-query-2", None), ("assistant-response-2", False), ("user-query-3", None), ("assistant-response-3", True)]
    result = preprocessor._process_context(fake_context, 6)

    assert (len(result.split("\n")) == 6)
    assert "<context>" in result
    assert "</context>" in result

    assert ("assistant-response-1 [status: success]" in result)
    assert ("assistant-response-2 [status: failed]" in result)
    assert ("assistant-response-3 [status: success]" in result)

def test_process_context_smaller_context(preprocessor):
    # test if context provided is less that the k value
    fake_context = [("user-query-1", None), ("assistant-response-1", None)]
    result = preprocessor._process_context(fake_context, 6)
    
    assert (len(result.split("\n")) == 2)
    assert "<context>" in result
    assert "</context>" in result

    result = result.replace("<context>", "")
    result = result.replace("</context>", "")
    result = result.split("\n")

    assert all(result[i] == fake_context[i] for i in range(-2,0,-1))

async def test_chat_context():
    class FakeChatStore:
        def __init__(self):
            self.history: list[tuple[str, bool | None]] = []

        def store_query_result(self, conversation_id: str, query: str, response: str, alarm: str):
            self.history.append((query, None))
            self.history.append((response, None))

        async def context_search(self, conversation_id: str):
            return list(self.history)

    fake_db = FakeChatStore()
    preprocessor = QueryPreprocessor(fake_db, fake_db, None, 3)
    settings = get_settings()

    preprocessor.store_context("test-conv-id1", "test-query 1?", "response-1", f"am{settings.alarm_delim}nc{settings.alarm_delim}0001")
    preprocessor.store_context("test-conv-id1", "test-query 2?", "response-2", f"am{settings.alarm_delim}nc{settings.alarm_delim}0001")

    results = await preprocessor._retrieve_context("test-conv-id1")

    assert len(results) >= 2
    assert any(entry[0] == "test-query 1?" for entry in results)
    assert any(entry[0] == "test-query 2?" for entry in results)
    assert any(entry[0] == "response-1" for entry in results)
    assert any(entry[0] == "response-2" for entry in results)
