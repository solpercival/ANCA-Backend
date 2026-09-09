"""Provider adapters for embeddings and generation.

This keeps the app switchable across Ollama, OpenAI-compatible APIs, and
Anthropic/Claude without changing the retrieval/storage layer.
"""
from __future__ import annotations

from typing import Any

import httpx

from rag_engine.config import get_settings


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
