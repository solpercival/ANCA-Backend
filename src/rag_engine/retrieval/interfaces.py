"""Protocols for the retrieval components.

Keeping these as interfaces is what lets CI run on hosted (CPU) runners:
tests inject fakes, while the real Qwen3-backed implementations load only at
runtime inside the model containers.
"""
from dataclasses import dataclass, field
from typing import Protocol
import json

@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    metadata: dict[str, str] = field(default_factory=dict)
    score: float = 0.0

    def __str__(self):
        return json.dumps(self.__dict__, default=str)

@dataclass
class Alarm:
    code: str
    title: str
    domain: str
    severity_score: int
    severity_category: str
    alarm_text: str
    data_fields: dict

class DenseEmbedder(Protocol):
    async def dense_embed(self, texts: list[str]) -> list[list[float]]: ...

class SparseEmbedder(Protocol):
    async def sparse_embed(self, texts: list[str]) -> list[dict[int, float]]: ...
    
class VectorStore(Protocol):
    async def semantic_search(
        self, vector: list[float], top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]: ...


class LexicalIndex(Protocol):
    async def lexical_search(self, vector: dict[int,float], top_k: int) -> list[Chunk]: ...


class AlarmStore(Protocol):
    async def alarm_search(self, request_json: dict) -> Alarm: ...

class Reranker(Protocol):
    async def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]: ...


class Generator(Protocol):
    async def generate(self, prompt: str) -> str: ...