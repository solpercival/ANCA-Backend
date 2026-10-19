"""Protocols for the retrieval components.

Keeping these as interfaces is what lets CI run on hosted (CPU) runners:
tests inject fakes, while the real Qwen3-backed implementations load only at
runtime inside the model containers.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from rag_engine.api.schemas import EffortSettings


@dataclass
class Chunk:
    """A piece of documentation as retrieved and ranked."""

    chunk_id: str
    text: str
    source: str  # document path
    metadata: dict[str, str] = field(default_factory=dict)
    # meaning depends on the last stage that set it: RRF score after fusion,
    # relevance probability (0-1) after the Qwen3 reranker
    score: float = 0.0
    # text of the heading the chunk sits under (its closest heading); None when the
    # chunk has none. Reported to clients as the citation's section.
    section: str | None = None

    @property
    def context_text(self) -> str:
        """The text under its heading path (metadata.heading_path, written by
        ingestion), e.g. "Device firmware upgrade > Prerequisites" then the text.
        A list or table cut out of its section does not say what it belongs to; the
        reranker judges this instead of `text` so that it can tell. Just `text` for
        a chunk ingested without a heading path."""
        path = (self.metadata or {}).get("heading_path")
        return f"{path}\n{self.text}" if path else self.text

    def __str__(self):
        return json.dumps(self.__dict__, default=str)


@dataclass
class Alarm:
    """An alarm catalogue record. Identifies the alarm; it is not documentation,
    so its text is never used as a source of guidance."""

    code: str
    title: str
    domain: str
    severity_score: int
    severity_category: str
    alarm_text: str
    data_fields: dict
    # the condition in the documentation's own terms, with no values from one
    # occurrence; what the docs are searched with when present ("" = none)
    description: str = ""


class DenseEmbedder(Protocol):
    """Text -> dense vectors (one per input, semantic_dim long)."""

    async def dense_embed(self, texts: list[str]) -> list[list[float]]:
        """Embed each text; the result has one vector per input, in input order."""


class SparseEmbedder(Protocol):
    """Text -> sparse term-weight vectors {vocab index: weight} (e.g. SPLADE)."""

    async def sparse_embed(self, texts: list[str]) -> list[dict[int, float]]:
        """Embed each text; the result has one sparse vector per input, in input order."""


# Retrieval filter passed as `where`; every key is optional and all present keys
# must match (AND):
#   "machine_variant": str        -- chunk metadata machine_variant equals it
#   "versions": list[str]         -- chunk metadata versions contains all of them
#   "doc_audiences": list[str]    -- DocAudience values (auth/tiers.py); the chunk's
#                                    document must lie in one of their folders.
#                                    Absent = all documents (set from the caller's tier)
Where = dict[str, Any]


class VectorStore(Protocol):
    """Nearest-neighbour search over dense embeddings, filtered by `where` (see Where)."""

    async def semantic_search(
        self, vector: list[float], top_k: int, where: Where | None = None
    ) -> list[Chunk]:
        """Up to top_k chunks nearest to the query `vector`, closest first."""


class LexicalIndex(Protocol):
    """Search over sparse embeddings; same `where` filters as VectorStore."""

    async def lexical_search(
        self, vector: dict[int, float], top_k: int, where: Where | None = None
    ) -> list[Chunk]:
        """Up to top_k chunks best matching the sparse query `vector`, best first."""


class SectionStore(Protocol):
    """The whole documentation section a chunk was cut from."""

    async def section_texts(self, chunk_ids: list[str]) -> dict[str, tuple[str, str]]:
        """chunk id -> (section id, the section's full text: every chunk under the
        same heading, in document order). Chunks with no heading are left out."""


class ResponseCache(Protocol):
    """Generated answers kept for reuse, looked up by the exact text that produced them."""

    async def retrieve_response(self, query: str) -> str | None:
        """The answer stored under `query`, or None when there is none."""

    async def add_response(self, query: str, response: str) -> None:
        """Store `response` under `query`."""


class AlarmStore(Protocol):
    """Alarm catalogue lookup; None for an unknown code."""

    async def get_alarm(self, code: str) -> Alarm | None:
        """The record for a full alarm code such as "am.fb.0002", or None."""


class Reranker(Protocol):
    """Reorders candidates by relevance to the query; returns at most top_n."""

    async def rerank(self, query: str, chunks: list[Chunk], effort: EffortSettings) -> list[Chunk]:
        """The best effort.reranker_n of `chunks` for `query`, most relevant first."""


class Generator(Protocol):
    """Prompt -> completion text from the LLM."""

    async def generate(
        self,
        prompt: str,
        tokens: int | None = None,
        thinking: bool = False,
        deterministic: bool = False,
    ) -> str:
        """Complete `prompt`. `tokens` caps the output length (None: provider default);
        `thinking` lets the model reason first where the provider supports it;
        `deterministic` asks for repeatable output (temperature 0 + fixed seed)
        where the provider supports it."""


class KeywordStore(Protocol):
    """Domain keywords (from the ingested docs) that match a query."""

    async def keyword_search(self, query: str, top_k: int) -> list[str]:
        """Up to top_k keywords matching the words of `query`, best match first."""


class ChatStore(Protocol):
    """Conversation history: read past turns, record new ones."""

    async def context_search(self, conversation_id: str) -> list[tuple[str, bool | None]]:
        """The conversation's messages, oldest first, as (text, feedback) pairs.
        feedback is True/False if the user marked a reply as working or not, else None."""

    def store_query_result(
        self, conversation_id: str, query: str, response: str, alarm_str: str | None
    ) -> int | None:
        """Record one finished turn; alarm_str is the alarm code it was about, if any.
        Returns the stored turn's response_id, or None if nothing was stored.

        Sync (blocking): run it in a thread if you call it from async code.
        """

    async def set_feedback(self, conversation_id: str, response_id: int, helpful: bool) -> bool:
        """Record whether the reply in turn response_id helped. False when no turn
        with that id exists in the conversation."""
