"""Protocols for the retrieval components.

Keeping these as interfaces is what lets CI run on hosted (CPU) runners:
tests inject fakes, while the real Qwen3-backed implementations load only at
runtime inside the model containers.
"""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    metadata: dict[str, str] = field(default_factory=dict)
    score: float = 0.0


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    async def search(
        self, vector: list[float], top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]: ...


class LexicalIndex(Protocol):
    async def search(self, query: str, top_k: int) -> list[Chunk]: ...


class Reranker(Protocol):
    async def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]: ...


class Generator(Protocol):
    async def generate(self, prompt: str) -> str: ...