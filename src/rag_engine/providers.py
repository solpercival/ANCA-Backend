"""Provider adapters for embeddings and generation.

Onboarding note:
- this module is the first integration point for model-provider switching
- each backend should implement the same interface contract used by the app
- current status: config exists and adapters are present for Ollama/OpenAI/
  Anthropic, but the real app wiring still needs to be validated end-to-end
- follow-up work: connect this layer into the actual retrieval and orchestrator
  runtime, then test a real provider on a full stack
"""
from __future__ import annotations

from typing import Any

from pathlib import Path

import httpx

from rag_engine.config import get_settings
from rag_engine.retrieval.interfaces import Chunk

class BM25LexicalIndex: 
    """BM25-backed lexical index. 

    Keep all bm25s-specific code inside this class so the rest of the app
    depends only on the LexicalIndex protocol.
    """
    
    def __init__(self, index_dir: str | None = None):
        self._index_dir = Path(index_dir or get_settings().bm25_index_dir)
        self._index = None
        self._corpus: list[str] = []
        self._metadata: dict[str, dict[str, str]] = {}
    
    def _load_library(self):
        # Import is intentionally kept here, inside the backend implementation
        import bm25s
        return bm25s
    
    def index_documents(self, chunks: list[Chunk]) -> None:
        bm25s = self._load_library()

        self._corpus = [chunk.text for chunk in chunks]
        self._metadata = {
            chunk.chunk_id: {"source": chunk.source, **chunk.metadata}
            for chunk in chunks
        }

        # This is just a shape example; the real API may differ slightly 
        # depending on the bm25s version we are using 
        self._index = bm25s.BM25()
        self._index.index(bm25s.tokenize(self._corpus))
        self._index.save(str(self._index_dir), corpus = self._corpus)

        # Store chunk metadata for reconstruction in search results
        self._index_dir.mkdir(parents=True, exist_ok=True)

    async def search(self, query: str, top_k: int) -> list[Chunk]:
        if not self._index:
            raise RuntimeError("BM25 lexical index has not been initialized")
        
        bm25s = self._load_library()

        # This is just an example adapt to what the API requires
        # The exact call maybe:
        # results = self_index.search(bm25s.tokenize([query]), top_k=top_k)
        # or similar depending on library version
        tokens = bm25s.tokenize([query])[0]
        results = self._index.search(tokens, top_k=top_k)

        out: list[Chunk] = []
        for item in results:
            chunk_id = str(item["chunk_id"])
            text = str(item["text"])
            source = str(item.get("source", "unknown"))
            metadata = dict(item.get("metadata", {}))

            out.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=text,
                    source=source,
                    metadata=metadata,
                )
            )
        return out

def get_lexical_backend() -> Any:
    settings = get_settings()
    provider = settings.lexical_provider.lower()

    if provider == "bm25":
        return BM25LexicalIndex()
    
    raise ValueError(f"Unsupported lexical provider: {provider}")

class OllamaEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/embed",
                json={"model": settings.embedding_model, "input": texts},
            )
        response.raise_for_status()
        payload = response.json()
        return payload["embeddings"]


class OpenAIEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when embedding_provider=openai")
        base_url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{base_url}/embeddings",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_embedding_model,
                    "input": texts,
                },
            )
        response.raise_for_status()
        payload = response.json()
        return [item["embedding"] for item in payload["data"]]


class AnthropicEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not expose embeddings in the current provider layer.")

class BAAIEmbedder:
    async def dense_embed(self, texts: list[str]) -> dict[list]:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.tei_endpoint.rstrip('/')}/embed",
                json={"inputs": texts},
            )
        response.raise_for_status()
        return response.json()

    async def sparse_embed(self, texts: list[str]) -> dict[list]:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.tei_endpoint.rstrip('/')}/embed-sparse",
                json={"inputs": texts},
            )
        response.raise_for_status()
        return response.json()
    
class OllamaGenerator:
    async def generate(self, prompt: str) -> str:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                json={"model": settings.llm_model, "prompt": prompt, "stream": False},
            )
        response.raise_for_status()
        payload = response.json()
        return payload["response"]


class OpenAIGenerator:
    async def generate(self, prompt: str) -> str:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when llm_provider=openai")
        base_url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]


class AnthropicGenerator:
    async def generate(self, prompt: str) -> str:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when llm_provider=anthropic")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.anthropic_base_url.rstrip('/')}/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.anthropic_llm_model,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        response.raise_for_status()
        payload = response.json()
        return payload["content"][0]["text"]


def get_embedding_backend() -> Any:
    settings = get_settings()
    provider = settings.embedding_provider.lower()
    if provider == "ollama":
        return OllamaEmbedder()
    if provider == "openai":
        return OpenAIEmbedder()
    if provider == "anthropic":
        return AnthropicEmbedder()
    raise ValueError(f"Unsupported embedding provider: {provider}")


def get_generation_backend() -> Any:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaGenerator()
    if provider == "openai":
        return OpenAIGenerator()
    if provider == "anthropic":
        return AnthropicGenerator()
    raise ValueError(f"Unsupported LLM provider: {provider}")


async def embed_texts(texts: list[str]) -> list[list[float]]:
    backend = get_embedding_backend()
    return await backend.embed(texts)


async def generate_text(prompt: str) -> str:
    backend = get_generation_backend()
    return await backend.generate(prompt)
