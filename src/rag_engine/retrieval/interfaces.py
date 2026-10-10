"""Protocols for the retrieval components.

Keeping these as interfaces is what lets CI run on hosted (CPU) runners:
tests inject fakes, while the real Qwen3-backed implementations load only at
runtime inside the model containers.
"""

import json
from dataclasses import dataclass, field
from typing import Protocol

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


class DenseEmbedder(Protocol):
    """Text -> dense vectors (one per input, semantic_dim long)."""

    async def dense_embed(self, texts: list[str]) -> list[list[float]]:
        """Embed each text; the result has one vector per input, in input order."""


class SparseEmbedder(Protocol):
    """Text -> sparse term-weight vectors {vocab index: weight} (e.g. SPLADE)."""

    async def sparse_embed(self, texts: list[str]) -> list[dict[int, float]]:
        """Embed each text; the result has one sparse vector per input, in input order."""


class VectorStore(Protocol):
    """Nearest-neighbour search over dense embeddings. `where` filters on chunk
    metadata (machine_variant, versions)."""

    async def semantic_search(
        self, vector: list[float], top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]:
        """Up to top_k chunks nearest to the query `vector`, closest first."""


class LexicalIndex(Protocol):
    """Search over sparse embeddings; same `where` filters as VectorStore."""

    async def lexical_search(
        self, vector: dict[int, float], top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]:
        """Up to top_k chunks best matching the sparse query `vector`, best first."""


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

    async def generate(self, prompt: str, tokens: int | None = None, thinking: bool = False) -> str:
        """Complete `prompt`. `tokens` caps the output length (None: provider default);
        `thinking` lets the model reason first where the provider supports it."""


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
    ) -> None:
        """Record one finished turn; alarm_str is the alarm code it was about, if any.

        Sync (blocking): run it in a thread if you call it from async code.
        """
