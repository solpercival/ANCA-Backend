import pytest
from rag_engine.retrieval.rewriter import Query, QueryPreprocessor

@pytest.fixture(scope="module")
def preprocessor():
    return QueryPreprocessor(
        keyword_db=None,
        rewrite_model=None,
        keywd_k=5,
        context_k=3
    )

# Query class initialization tests
def test_query_initialization():
    context = ["user: hello", "assist: hi there"]
    query = Query("what is this?", context)
    
    assert query.resolved_query == "what is this?"
    assert query.context == context
    assert query.lexical_tokens == []

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
    result = preprocessor._process_context([])
    assert result == ""

def test_process_context_basic(preprocessor):
    fake_context = ["user-query-1", "assistant-response-1", "user-query-2", "assistant-response-2", "user-query-3", "assistant-response-3"]
    result = preprocessor._process_context(fake_context, 3)

    assert (len(result.split("\n")) == 3)
    assert "<context>" in result
    assert "</context>" in result

    result = result.replace("<context>", "")
    result = result.replace("</context>", "")
    result = result.split("\n")

    assert all(result[i] == fake_context[i] for i in range(-3,0,-1))

def test_process_context_smaller_context(preprocessor):
    # test if context provided is less that the k value
    fake_context = ["user-query-1", "assistant-response-1"]
    result = preprocessor._process_context(fake_context, 6)
    
    assert (len(result.split("\n")) == 2)
    assert "<context>" in result
    assert "</context>" in result

    result = result.replace("<context>", "")
    result = result.replace("</context>", "")
    result = result.split("\n")

    assert all(result[i] == fake_context[i] for i in range(-2,0,-1))