"""Provider adapters for embeddings, generation and storage, plus the factories
that pick one from settings.

Each adapter implements an interface from retrieval/interfaces.py, so the
orchestrator never knows which vendor it talks to. orchestrator.get_orchestrator
calls the get_*_backend factories; the *_PROVIDER settings choose:

    DENSE_EMBEDDING_PROVIDER   ollama | openai            -> OllamaEmbedder | OpenAIEmbedder
    SPARSE_EMBEDDING_PROVIDER  huggingface_tei            -> TEIEmbedder (dual setup only)
    LLM_PROVIDER               ollama | openai | anthropic -> *Generator
                               (query rewriting supports ollama only)
    LEXICAL_PROVIDER / CHAT_STORE_PROVIDER  postgres      -> PostgresDBConnection

The Ollama path is the one exercised end to end by `make bench` / `make eval`;
the OpenAI and Anthropic adapters are not run there. All adapters share
the app's httpx client, whose timeouts are set in main.lifespan.
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

# a qwen3 reasoning trace, closed or cut off at the end of the output
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


# --- storage backends --------------------------------------------------------------

def get_lexical_backend() -> Any:
    """LexicalIndex for sparse search (only used when EMBEDDING_SETUP=dual)."""
    settings = get_settings()
    provider = settings.lexical_provider.lower()

    if provider == "postgres":
        return PostgresDBConnection()
    
    raise ValueError(f"Unsupported lexical provider: {provider}")

def get_chat_store_backend() -> Any:
    """ChatStore holding conversation history for query rewriting."""
    settings = get_settings()
    provider = settings.chat_store_provider.lower()

    if provider == "postgres":
        return PostgresDBConnection()

    raise ValueError(f"Unsupported chat store provider: {provider}")
    
def get_alarm_store_backend() -> Any:
    """Unused: get_orchestrator builds stores.alarms.PostgresAlarmStore directly.
    Note this returns PostgresDBConnection, which has no get_alarm method, so it
    does not satisfy AlarmStore."""
    settings = get_settings()
    provider = settings.alarm_store_provider.lower()

    if provider == "postgres":
        return PostgresDBConnection()
    
    raise ValueError(f"Unsupported alarm store provider: {provider}")
    
# --- embedders ---------------------------------------------------------------------

class OllamaEmbedder:
    """DenseEmbedder via Ollama's /api/embed (EMBEDDING_MODEL)."""

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
    """DenseEmbedder via an OpenAI-compatible /embeddings endpoint (OPENAI_BASE_URL).

    The vector size must equal SEMANTIC_DIM and the vector(1024) column, so switching
    model generally means a new migration and a full re-ingest.
    """

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
    """Placeholder: Anthropic has no embeddings API. Never returned by a factory."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not expose embeddings in the current provider layer.")

class TEIEmbedder:
    """SparseEmbedder via Hugging Face Text Embeddings Inference /embed_sparse
    (SPLADE, TEI_ENDPOINT). Returns {vocab index: weight} per input."""

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
    
# --- generators ----------------------------------------------------------------------

class OllamaGenerator:
    """Generator for answers via Ollama /api/generate (LLM_MODEL), streamed.

    Output is capped at LLM_NUM_PREDICT tokens and any reasoning trace is stripped.
    Timing stats are logged as generate_stats (read by scripts/bench.sh).
    """

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def generate(self, prompt: str, tokens: int | None = None, thinking: bool = False) -> str:
        settings = get_settings()
        # stream so the connection stays alive between tokens (avoids ReadTimeout on
        # slow CPU generations) and cap num_predict, the biggest CPU-side latency lever
        chunks: list[str] = []
        generate_payload = {
            "model": settings.llm_model,
            "prompt": prompt,
            "stream": True,
            # skip qwen3's hidden reasoning trace, which otherwise burns num_predict
            # tokens before any answer text is produced
            "think": thinking,
            "options": {},
        }

        if tokens:
            generate_payload["options"]["num_predict"] = tokens
        
        async with self._client.stream(
            "POST",
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json=generate_payload,
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
    """Generator for query rewriting (retrieval/rewriter.py) with the small
    REWRITE_MODEL and its own REWRITE_NUM_PREDICT cap."""

    def __init__(self, client: httpx.AsyncClient):
            self._client = client
    
    async def generate(self, prompt: str, tokens: int | None = None, thinking: bool = False) -> str:
        settings = get_settings()

        # similar to OllamaGenerator, slight modifications to account for longer prompt sizes.
        chunks: list[str] = []
        generate_payload = {
            "model": settings.rewrite_model,
            "prompt": prompt,
            "stream": True,
        }

        if tokens:
            generate_payload["options"]["num_predict"] = tokens

        async with self._client.stream(
            "POST",
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json=generate_payload,
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
    """Generator via an OpenAI-compatible /chat/completions endpoint (OpenAI,
    OpenRouter, LiteLLM...). Non-streaming; no output-token cap is set."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def generate(self, prompt: str, tokens: int | None = None, thinking: bool = False | None) -> str:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when llm_provider=openai")
        base_url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")

        generate_payload = {
            "model": settings.openai_llm_model, 
            "messages": [{"role": "user", "content": prompt}],
        }

        if tokens:
            generate_payload["max_completion_tokens"] = tokens

        if thinking:
            generate_payload["reasoning_effort"] = "high"

        response = await self._client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json=generate_payload,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]


class AnthropicGenerator:
    """Generator via the Anthropic Messages API (ANTHROPIC_LLM_MODEL), non-streaming,
    max_tokens 1024."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def generate(self, prompt: str, tokens: int | None = None, thinking: bool = False) -> str:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when llm_provider=anthropic")

        generate_payload = {
            "model": settings.anthropic_llm_model,
            "messages": [{"role": "user", "content": prompt}]
        }

        if tokens:
            generate_payload["max_tokens"] = tokens

        if thinking:
            generate_payload["thinking"] = { "type": "enabled", "budget_tokens": 1024}
        else:
            generate_payload["thinking"] = { "type": "disabled" }


        response = await self._client.post(
            f"{settings.anthropic_base_url.rstrip('/')}/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=generate_payload
        )
        
        response.raise_for_status()
        payload = response.json()
        return payload["content"][0]["text"]

# --- factories (selected by the *_PROVIDER settings) ---------------------------------

def get_dense_embedding_backend(client: httpx.AsyncClient) -> Any:
    """DenseEmbedder for DENSE_EMBEDDING_PROVIDER; ValueError for an unknown name."""
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
    """SparseEmbedder for SPARSE_EMBEDDING_PROVIDER; ValueError for an unknown name."""
    settings = get_settings()
    provider = settings.sparse_embedding_provider.lower()

    if provider == "huggingface_tei":
        return TEIEmbedder(client)

    raise ValueError(f"Unsupported embedding provider: {provider}")

def get_generation_backend(client: httpx.AsyncClient) -> Any:
    """Answer Generator for LLM_PROVIDER; ValueError for an unknown name."""
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
    """Query-rewrite Generator. Only Ollama is supported, so LLM_PROVIDER=openai or
    anthropic currently makes get_orchestrator fail here."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaRewriteGenerator(client)
    raise ValueError(f"Unsupported LLM provider: {provider}")

async def generate_text(prompt: str, client: httpx.AsyncClient) -> str:
    """One-off generation with the configured provider (not used by the app itself)."""
    backend = get_generation_backend(client)
    return await backend.generate(prompt, None, False)