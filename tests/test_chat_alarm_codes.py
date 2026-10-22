"""A chat message that names an alarm code searches and reranks with what the alarm
is about, and the model is told which alarm the code is: the documentation never
mentions codes ("What does am.fb.0002 mean?")."""

import asyncio

from rag_engine.api.schemas import ChatRequest
from rag_engine.auth.tiers import Tier
from rag_engine.orchestrator import Orchestrator
from rag_engine.retrieval.interfaces import Chunk
from tests.fakes import FB_0002, FakeAlarmStore, FakePreprocessor


class RecordingRetriever:
    def __init__(self):
        self.queries: list[str] = []

    async def retrieve(self, query, top_k, where=None):
        self.queries.append(query)
        return [Chunk(chunk_id="c1", text="Reinitialise the EtherCAT bus.", source="coe.md")]


class Reranker:
    def __init__(self):
        self.queries: list[str] = []

    async def rerank(self, query, chunks, effort):
        self.queries.append(query)
        return chunks


class Generator:
    def __init__(self):
        self.prompt = ""

    async def generate(self, prompt, tokens=None, thinking=False, deterministic=False):
        self.prompt = prompt
        return "Reinitialise the EtherCAT bus."


def _chat(message):
    retriever, reranker, generator = RecordingRetriever(), Reranker(), Generator()
    orch = Orchestrator(FakePreprocessor(), retriever, reranker, generator, FakeAlarmStore())
    asyncio.run(orch.chat(ChatRequest(conversation_id="c1", message=message), Tier.technician))
    assert reranker.queries == retriever.queries
    return retriever.queries[0], generator.prompt


def test_a_named_alarm_code_is_searched_by_what_the_alarm_is_about():
    question = f"What does {FB_0002.code.upper()} mean?"
    query, prompt = _chat(question)

    assert FB_0002.title in query
    assert f"{FB_0002.code} = {FB_0002.title}." in prompt
    assert prompt.endswith(f"User: {question}")


def test_unknown_codes_and_plain_questions_search_as_asked():
    for question in ("What does zz.qq.9999 mean?", "How does lookahead work?"):
        query, prompt = _chat(question)
        assert query == question
        assert "Alarm codes in the question" not in prompt
