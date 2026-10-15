"""Shared test doubles."""

from rag_engine.auth.tiers import DocAudience
from rag_engine.retrieval.interfaces import Alarm, Chunk

DOCS = "docs/docs-proto/starter-kit/docs"
USER_GUIDE_DOC = f"{DOCS}/user-guide/troubleshoot/coe-device-errors.md"
PPR_DOC = f"{DOCS}/part-programmers-reference/05-functions.md"

FB_0002 = Alarm(
    code="am.fb.0002",
    title="EtherCAT slave lost",
    domain="Fieldbus",
    severity_score=900,
    severity_category="error",
    alarm_text="EtherCAT slave 3 stopped responding.",
    data_fields={},
)


class FakeAlarmStore:
    """In-memory catalogue; unknown codes return None like the real store."""

    def __init__(self, *alarms: Alarm):
        self._alarms = {a.code: a for a in (alarms or (FB_0002,))}

    async def get_alarm(self, code: str) -> Alarm | None:
        return self._alarms.get(code)


class FakeEmbedder:
    """Dense and sparse embedder returning a fixed vector per text."""

    async def dense_embed(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    async def sparse_embed(self, texts):
        return [{1: 0.5} for _ in texts]


class FakeDocStore:
    """VectorStore + LexicalIndex over fixed chunks that honours where["doc_audiences"]
    like the Postgres search (document path contains an allowed audience folder).
    Records each call's `where` as (search kind, where)."""

    def __init__(self, *chunks: Chunk):
        self._chunks = list(chunks)
        self.calls = []

    def _search(self, kind, top_k, where):
        self.calls.append((kind, where))
        chunks = self._chunks
        if where and "doc_audiences" in where:
            fragments = [DocAudience(a).path_fragment for a in where["doc_audiences"]]
            chunks = [c for c in chunks if any(f in c.source for f in fragments)]
        return chunks[:top_k]

    async def semantic_search(self, vector, top_k, where=None):
        return self._search("semantic", top_k, where)

    async def lexical_search(self, vector, top_k, where=None):
        return self._search("lexical", top_k, where)


class FakePreprocessor:
    """Passes the query through unchanged and stores no conversation context."""

    async def process_prompt(self, raw_query, conversation_id, effort):
        return raw_query

    def store_context(self, conversation_id, query, response, alarm):
        return
