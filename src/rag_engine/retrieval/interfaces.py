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

    async def dense_embed(self, texts: list[str]) -> list[list[float]]: ...


class SparseEmbedder(Protocol):
    """Text -> sparse term-weight vectors {vocab index: weight} (e.g. SPLADE)."""

    async def sparse_embed(self, texts: list[str]) -> list[dict[int, float]]: ...


class VectorStore(Protocol):
    """Nearest-neighbour search over dense embeddings. `where` filters on chunk
    metadata (machine_variant, versions)."""

    async def semantic_search(
        self, vector: list[float], top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]: ...


class LexicalIndex(Protocol):
    """Search over sparse embeddings; same `where` filters as VectorStore."""

    async def lexical_search(
        self, vector: dict[int, float], top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]: ...


class AlarmStore(Protocol):
    """Alarm catalogue lookup; None for an unknown code."""

    async def get_alarm(self, code: str) -> Alarm | None: ...


class Reranker(Protocol):
    """Reorders candidates by relevance to the query; returns at most top_n."""

    async def rerank(
        self, query: str, chunks: list[Chunk], effort: EffortSettings
    ) -> list[Chunk]: ...


class Generator(Protocol):
    """Prompt -> completion text from the LLM."""

    async def generate(
        self, prompt: str, tokens: int | None = None, thinking: bool = False
    ) -> str: ...


class KeywordStore(Protocol):
    """Domain keywords (from the ingested docs) that match a query."""

    async def keyword_search(self, query: str, top_k: int) -> list[str]: ...


class ChatStore(Protocol):
    """Conversation history: read past turns, record new ones."""

    async def context_search(self, conversation_id: str) -> list[tuple[str, bool | None]]: ...

    # sync: called from sync code; run it in a thread if you call it from async code
    def store_query_result(
        self, conversation_id: str, query: str, response: str, alarm_str: str | None
    ) -> None: ...
