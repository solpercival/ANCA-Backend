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

import httpx

from rag_engine.config import get_settings
from rag_engine.stores.search import PostgresDBConnection


def get_lexical_backend() -> Any:
    settings = get_settings()
    provider = settings.lexical_provider.lower()

    if provider == "postgres":
        return PostgresDBConnection()
    
    raise ValueError(f"Unsupported lexical provider: {provider}")

class OllamaEmbedder:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def dense_embed(self, texts: list[str]) -> list[list[float]]:
        settings = get_settings()
        response = await self._client.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/embed",
            json={"model": settings.embedding_model, "input": texts},
        )

        response.raise_for_status()
        payload = response.json()
        return payload["embeddings"]


class OpenAIEmbedder:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        
    async def dense_embed(self, texts: list[str]) -> list[list[float]]:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when embedding_provider=openai")
        base_url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
        response = await self._client.post(
            f"{base_url}/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.openai_embedding_model, "input": texts}
        )
        response.raise_for_status()
        payload = response.json()
        return [item["embedding"] for item in payload["data"]]


class AnthropicEmbedder:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not expose embeddings in the current provider layer.")

class TEIEmbedder:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def sparse_embed(self, texts: list[str]) -> list[dict[int, float]]:
        settings = get_settings()
        response = await self._client.post(
            f"{settings.tei_endpoint.rstrip('/')}/embed_sparse",
            json={"inputs": texts},
        )
        sparse_vecs = response.raise_for_status().json()

        return [{int(entry["index"]): float(entry["value"]) for entry in sparse_chunk} for sparse_chunk in sparse_vecs]
    
class OllamaGenerator:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def generate(self, prompt: str) -> str:
        settings = get_settings()
        response = await self._client.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={"model": settings.llm_model, "prompt": prompt, "stream": False},
        )
        
        response.raise_for_status()
        payload = response.json()
        return payload["response"]


class OpenAIGenerator:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def generate(self, prompt: str) -> str:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when llm_provider=openai")
        base_url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")

        response = await self._client.post(
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
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def generate(self, prompt: str) -> str:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when llm_provider=anthropic")

        response = await self._client.post(
            f"{settings.anthropic_base_url.rstrip('/')}/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.anthropic_llm_model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        response.raise_for_status()
        payload = response.json()
        return payload["content"][0]["text"]

def get_dense_embedding_backend(client: httpx.AsyncClient) -> Any:
    settings = get_settings()
    provider = settings.dense_embedding_provider.lower()

    if provider == "ollama":
        return OllamaEmbedder(client)

    if provider == "openai":
        return OpenAIEmbedder(client)

    if provider == "anthropic":
        return AnthropicEmbedder(client)
    
    raise ValueError(f"Unsupported embedding provider: {provider}")

def get_sparse_embedding_backend(client: httpx.AsyncClient) -> Any:
    settings = get_settings()
    provider = settings.sparse_embedding_provider.lower()

    if provider == "huggingface_tei":
        return TEIEmbedder(client)

    raise ValueError(f"Unsupported embedding provider: {provider}")

def get_generation_backend(client: httpx.AsyncClient | None = None) -> Any:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaGenerator(client)
    if provider == "openai":
        return OpenAIGenerator(client)
    if provider == "anthropic":
        return AnthropicGenerator(client)
    raise ValueError(f"Unsupported LLM provider: {provider}")


async def generate_text(prompt: str) -> str:
    backend = get_generation_backend()
    return await backend.generate(prompt)
