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

import json
import logging
import re
from typing import Any

import httpx

from rag_engine.config import get_settings
from rag_engine.stores.search import PostgresDBConnection

log = logging.getLogger("rag_engine.providers")

_THINK_SPAN = re.compile(r"<think>.*?(?:</think>|$)", re.DOTALL)


def _log_generate_stats(final: dict) -> None:
    """Split Ollama's generation time into prompt reading and answer writing.

    The last streamed message carries token counts and nanosecond durations;
    low output tok/s points at GPU placement, a big prompt_secs at context size.
    """
    def secs(key: str) -> float:
        return (final.get(key) or 0) / 1e9

    def rate(count_key: str, duration_key: str) -> float:
        d = secs(duration_key)
        return (final.get(count_key) or 0) / d if d else 0.0

    log.info(
        "generate_stats prompt_tokens=%s prompt_secs=%.2f prompt_tok_s=%.0f "
        "output_tokens=%s output_secs=%.2f output_tok_s=%.1f load_secs=%.2f "
        "total_secs=%.2f done_reason=%s",
        final.get("prompt_eval_count"), secs("prompt_eval_duration"),
        rate("prompt_eval_count", "prompt_eval_duration"),
        final.get("eval_count"), secs("eval_duration"), rate("eval_count", "eval_duration"),
        secs("load_duration"), secs("total_duration"), final.get("done_reason"),
    )


def get_lexical_backend() -> Any:
    settings = get_settings()
    provider = settings.lexical_provider.lower()

    if provider == "postgres":
        return PostgresDBConnection()
    
    raise ValueError(f"Unsupported lexical provider: {provider}")

def get_chat_store_backend() -> Any:
    settings = get_settings()
    provider = settings.chat_store_provider.lower()

    if provider == "postgres":
        return PostgresDBConnection()

    raise ValueError(f"Unsupported chat store provider: {provider}")
    
def get_alarm_store_backend() -> Any:
    settings = get_settings()
    provider = settings.alarm_store_provider.lower()

    if provider == "postgres":
        return PostgresDBConnection()
    
    raise ValueError(f"Unsupported alarm store provider: {provider}")
    
class OllamaEmbedder:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def dense_embed(self, texts: list[str]) -> list[list[float]]:
        settings = get_settings()
        response = await self._client.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/embed",
            json={
                "model": settings.embedding_model,
                "input": texts,
                # small context and (by default) CPU placement keep the query embedder
                # off the GPU budget, so the generator and the reranker fit on one card
                "options": {
                    "num_ctx": settings.embedding_num_ctx,
                    "num_gpu": settings.embedding_num_gpu,
                },
            },
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
        # stream so the connection stays alive between tokens (avoids ReadTimeout on
        # slow CPU generations) and cap num_predict, the biggest CPU-side latency lever
        chunks: list[str] = []
        async with self._client.stream(
            "POST",
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={
                "model": settings.llm_model,
                "prompt": prompt,
                "stream": True,
                # skip qwen3's hidden reasoning trace, which otherwise burns num_predict
                # tokens before any answer text is produced
                "think": False,
                "options": {"num_predict": settings.llm_num_predict},
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                payload = json.loads(line)
                chunks.append(payload.get("response", ""))
                if payload.get("done"):
                    _log_generate_stats(payload)
                    break
        # older Ollama versions ignore "think" and inline the trace; drop it, including
        # an unclosed span left when num_predict cuts generation off mid-thought
        return _THINK_SPAN.sub("", "".join(chunks)).strip()

class OllamaRewriteGenerator:
    def __init__(self, client: httpx.AsyncClient):
            self._client = client
    
    async def generate(self, prompt: str) -> str:
        settings = get_settings()

        # similar to OllamaGenerator, slight modifications to account for longer prompt sizes.
        chunks: list[str] = []
        async with self._client.stream(
            "POST",
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={
                "model": settings.rewrite_model,
                "prompt": prompt,
                "stream": True,
                "options": {"num_predict": settings.rewrite_num_predict},
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                payload = json.loads(line)
                chunks.append(payload.get("response", ""))
                if payload.get("done"):
                    break
        return "".join(chunks)

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
        raise ValueError(
            "Anthropic does not provide embeddings; choose 'ollama' or 'openai' "
            "for DENSE_EMBEDDING_PROVIDER"
        )
    
    raise ValueError(f"Unsupported embedding provider: {provider}")

def get_sparse_embedding_backend(client: httpx.AsyncClient) -> Any:
    settings = get_settings()
    provider = settings.sparse_embedding_provider.lower()

    if provider == "huggingface_tei":
        return TEIEmbedder(client)

    raise ValueError(f"Unsupported embedding provider: {provider}")

def get_generation_backend(client: httpx.AsyncClient) -> Any:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaGenerator(client)
    if provider == "openai":
        return OpenAIGenerator(client)
    if provider == "anthropic":
        return AnthropicGenerator(client)
    raise ValueError(f"Unsupported LLM provider: {provider}")

def get_rewrite_backend(client: httpx.AsyncClient) -> Any:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaRewriteGenerator(client)
    raise ValueError(f"Unsupported LLM provider: {provider}")

async def generate_text(prompt: str, client: httpx.AsyncClient) -> str:
    backend = get_generation_backend(client)
    return await backend.generate(prompt)