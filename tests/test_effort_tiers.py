import json
import httpx
import pytest
from pydantic import ValidationError

from rag_engine.api.schemas import (
    ChatRequest,
    EffortLevel,
    EffortSettings,
    ResolveRequest,
    get_effort_settings,
)
from rag_engine.config import get_settings
from rag_engine.providers import OllamaGenerator
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker
from rag_engine.retrieval.rewriter import QueryPreprocessor


def test_resolve_req_default_medium_effort():
    req = ResolveRequest(code="am.fb.0002")
    assert req.effort == EffortLevel.MEDIUM
    assert req.effort == "medium"


def test_chat_req_default_medium_effort():
    req = ChatRequest(conversation_id="conv-1", message="How to reset?")
    assert req.effort == EffortLevel.MEDIUM
    assert req.effort == "medium"


@pytest.mark.parametrize("tier_str", ["low", "medium", "high"])
def test_resolve_req_accepts_effort_str(tier_str):
    req = ResolveRequest(code="am.fb.0002", effort=tier_str)
    assert req.effort == tier_str
    assert isinstance(req.effort, EffortLevel)


@pytest.mark.parametrize("tier_str", ["low", "medium", "high"])
def test_chat_req_accepts_effort_str(tier_str):
    req = ChatRequest(conversation_id="c-1", message="Help", effort=tier_str)
    assert req.effort == tier_str
    assert isinstance(req.effort, EffortLevel)


@pytest.mark.parametrize("invalid_effort", ["ultra", "extreme", "none", "", 123, False])
def test_resolve_request_rejects_invalid_effort(invalid_effort):
    with pytest.raises(ValidationError):
        ResolveRequest(code="am.fb.0002", effort=invalid_effort)


@pytest.mark.parametrize("invalid_effort", ["ultra", "extreme", "none", "", 999])
def test_chat_request_rejects_invalid_effort(invalid_effort):
    with pytest.raises(ValidationError):
        ChatRequest(conversation_id="c-1", message="Help", effort=invalid_effort)


def test_get_effort_settings_mapping():
    settings = get_settings()

    # Low tier
    low = get_effort_settings(EffortLevel.LOW)
    assert low.retrieval_k == settings.LOW_CONFIG["retrieval_k"]
    assert low.reranker_n == settings.LOW_CONFIG["reranker_n"]
    assert low.num_predict == settings.LOW_CONFIG["num_predict"]
    assert low.rewrite is False
    assert low.reranker == "identity"

    # Medium tier
    mid = get_effort_settings(EffortLevel.MEDIUM)
    assert mid.retrieval_k == settings.MID_CONFIG["retrieval_k"]
    assert mid.reranker_n == settings.MID_CONFIG["reranker_n"]
    assert mid.num_predict == settings.MID_CONFIG["num_predict"]
    assert mid.rewrite is True
    assert mid.thinking is False

    # High tier
    high = get_effort_settings(EffortLevel.HIGH)
    assert high.retrieval_k == settings.HIGH_CONFIG["retrieval_k"]
    assert high.reranker_n == settings.HIGH_CONFIG["reranker_n"]
    assert high.num_predict == settings.HIGH_CONFIG["num_predict"]
    assert high.rewrite is True
    assert high.thinking is True

    # None defaults to Medium
    default = get_effort_settings(None)
    assert default.retrieval_k == mid.retrieval_k
    assert default.num_predict == mid.num_predict


def test_api_resolve_endpoint_effort_boundary_validation(client, bearer):
    # Valid effort tiers return 200
    for effort in ("low", "medium", "high"):
        resp = client.post(
            "/api/v2/resolve",
            json={"code": "am.fb.0002", "effort": effort},
            headers=bearer,
        )
        assert resp.status_code == 200, f"Expected 200 for effort='{effort}', got {resp.status_code}"

    # Invalid effort tier rejected with 422
    resp_invalid = client.post(
        "/api/v2/resolve",
        json={"code": "am.fb.0002", "effort": "super_high"},
        headers=bearer,
    )
    assert resp_invalid.status_code == 422
    assert resp_invalid.json()["error"]["code"] == "validation_error"


def test_api_chat_endpoint_effort_boundary_validation(client, bearer):
    # Valid effort tiers return 200
    for effort in ("low", "medium", "high"):
        resp = client.post(
            "/api/v2/chat",
            json={"conversation_id": "c-1", "message": "how to fix", "effort": effort},
            headers=bearer,
        )
        assert resp.status_code == 200, f"Expected 200 for effort='{effort}', got {resp.status_code}"

    # Invalid effort tier rejected with 422
    resp_invalid = client.post(
        "/api/v2/chat",
        json={"conversation_id": "c-1", "message": "how to fix", "effort": "bad_tier"},
        headers=bearer,
    )
    assert resp_invalid.status_code == 422
    assert resp_invalid.json()["error"]["code"] == "validation_error"


def _make_chunks(n: int) -> list[Chunk]:
    return [Chunk(chunk_id=str(i), text=f"chunk {i}", source="manual.md") for i in range(n)]


async def test_identity_reranker_truncates_by_effort_reranker_n():
    chunks = _make_chunks(10)
    effort = EffortSettings(reranker_n=3)
    result = await IdentityReranker().rerank("query", chunks, effort=effort)
    assert len(result) == 3
    assert [c.chunk_id for c in result] == ["0", "1", "2"]


async def test_qwen3_reranker_truncates_by_effort_reranker_n():
    reranker = Qwen3Reranker()
    reranker._ensure_loaded = lambda: None
    reranker._score = lambda query, texts: [float(i) for i in range(len(texts))]

    chunks = _make_chunks(6)
    effort = EffortSettings(reranker_n=2)
    result = await reranker.rerank("query", chunks, effort=effort)
    assert len(result) == 2
    # Highest score chunks selected: 5 and 4
    assert [c.chunk_id for c in result] == ["5", "4"]


async def test_query_preprocessor_skips_rewrite_when_disabled():
    class RecordingGenerator:
        calls = 0
        async def generate(self, prompt: str, tokens: int | None = None, thinking: bool = False) -> str:
            self.calls += 1
            return "rewritten"

    generator = RecordingGenerator()
    preprocessor = QueryPreprocessor(
        chat_db=None,
        keyword_db=None,
        rewrite_model=generator,
        keywd_k=5,
    )

    effort_disabled = EffortSettings(rewrite=False)
    output = await preprocessor.process_prompt("what is this?", "conv-1", effort=effort_disabled)

    assert generator.calls == 0
    assert output == "what is this?"


async def test_query_preprocessor_calls_rewrite_with_num_rewrite_tokens():
    class FakeChatStore:
        async def context_search(self, conversation_id: str):
            return [("what is the alarm?", None), ("It is am.fb.0002", None)]

    class FakeKeywordStore:
        async def keyword_search(self, query: str, top_k: int):
            return ["ethercat"]

    class RecordingGenerator:
        calls = 0
        last_tokens = None
        async def generate(self, prompt: str, tokens: int | None = None, thinking: bool = False) -> str:
            self.calls += 1
            self.last_tokens = tokens
            return "standalone query for am.fb.0002"

    generator = RecordingGenerator()
    preprocessor = QueryPreprocessor(
        chat_db=FakeChatStore(),
        keyword_db=FakeKeywordStore(),
        rewrite_model=generator,
        keywd_k=5,
    )

    effort_enabled = EffortSettings(rewrite=True, num_rewrite=256, context_k=2)
    output = await preprocessor.process_prompt("how to fix it?", "conv-1", effort=effort_enabled)

    assert generator.calls == 1
    assert generator.last_tokens == 256
    assert output == "standalone query for am.fb.0002"


def test_query_preprocessor_process_context_respects_context_k():
    preprocessor = QueryPreprocessor(chat_db=None, keyword_db=None, rewrite_model=None)
    fake_history = [
        ("user query 1", None),
        ("assistant reply 1", None),
        ("user query 2", None),
        ("assistant reply 2", None),
    ]

    # prev_k = 2 should preserve only the last 2 turns
    formatted = preprocessor._process_context(fake_history, prev_k=2)
    assert "<context>" in formatted
    assert "user query 1" not in formatted
    assert "user query 2" in formatted
    assert "assistant reply 2" in formatted


async def test_ollama_generator_passes_num_predict_and_thinking_payload():
    captured = []

    def mock_handler(request: httpx.Request):
        captured.append(json.loads(request.content))
        # Return a valid Ollama streaming line
        line = json.dumps({"response": "answer", "done": True}) + "\n"
        return httpx.Response(200, text=line)

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        generator = OllamaGenerator(client)

        # Call 1: Low effort (num_predict=120, thinking=False)
        await generator.generate("prompt 1", tokens=120, thinking=False)
        assert len(captured) == 1
        assert captured[0]["options"]["num_predict"] == 120
        assert captured[0]["think"] is False

        # Call 2: High effort (num_predict=250, thinking=True)
        await generator.generate("prompt 2", tokens=250, thinking=True)
        assert len(captured) == 2
        assert captured[1]["options"]["num_predict"] == 250
        assert captured[1]["think"] is True
