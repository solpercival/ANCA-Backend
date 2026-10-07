"""Typed configuration loaded from environment (pydantic-settings).

Onboarding note:
- this file is the source of truth for runtime provider selection
- keep provider names and URLs here; do not hard-code model endpoints elsewhere
"""
from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_JWT_SECRET = "change-me-in-prod"


class Settings(BaseSettings):
    """All runtime settings. Each field is read from the environment variable of the
    same name (case-insensitive, e.g. POSTGRES_HOST), then from .env, then this
    default. Outside APP_ENV=local, the validators below refuse unsafe defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    allowed_hosts: list[str] = ["*"]  # must be named explicitly outside local
    gzip_minimum_size: int = 500      # bytes
    hsts_max_age: int = 63072000      # two years, the value HSTS preload lists expect

    # auth
    jwt_secret: str = LOCAL_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "anca-rag-engine"
    jwt_audience: str = "anca-frontend"
    access_token_ttl_minutes: int = 15   # bearer JWT lifetime
    refresh_token_idle_days: int = 7     # session ends if unused this long
    session_max_days: int = 30           # absolute session cap, however active
    auth_allow_registration: bool = False
    auth_cookie_secure: bool = True
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    login_max_attempts: int = 5
    login_max_attempts_per_ip: int = 20
    login_window_seconds: int = 900
    cors_allow_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # postgres
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "rag"
    postgres_user: str = "rag"
    postgres_password: str = "rag"

    # redis (sessions, rate limits; the chunk/response cache keys below are for
    # RedisConnection in stores/search.py, which nothing uses yet)
    redis_host: str = "redis"
    redis_port: int = 6379
    chunks_prefix: str = "chunks:"
    chunks_ttl: int = 3600
    response_prefix: str = "response:"
    response_ttl: int = 86400

    # rate limiting: requests per window, per client IP and per account tier
    rate_limit_window_seconds: int = 60
    resolve_rate_limit_per_ip: int = 30
    resolve_rate_limit_per_tier: int = 120
    chat_rate_limit_per_ip: int = 10
    chat_rate_limit_per_tier: int = 60
    max_request_body_bytes: int = 64 * 1024

    # provider selection: which backend implements each interface (see providers.py
    # and orchestrator.get_orchestrator for the accepted names)
    dense_embedding_provider: str = "ollama"
    sparse_embedding_provider: str = "huggingface_tei"
    lexical_provider: str = "postgres"
    llm_provider: str = "ollama"
    chat_store_provider: str = "postgres"
    alarm_store_provider: str = "postgres"

    # ollama
    ollama_base_url: str = "http://ollama:11434"
    embedding_model: str = "qwen3-embedding:0.6b"
    # instruct (non-thinking) build: plain qwen3:4b is the always-thinking 2507 model,
    # which ignores think:false and spends num_predict on reasoning text
    llm_model: str = "qwen3:4b-instruct-2507-q4_K_M"
    rewrite_model: str = "qwen3:0.6b"  # small model for query rewriting (retrieval/rewriter.py)
    # query-time embedding context. Ollama's default (4096) makes the 0.6B embedder
    # hold ~2.4 GB of VRAM; queries are short, and 1024 still covers the longest chat
    # message (4096 chars ~ 1k tokens). Longer input is truncated, not rejected.
    embedding_num_ctx: int = 1024
    # layers of the query embedder Ollama puts on the GPU; 0 = CPU. One short query per
    # request is cheap on CPU and frees ~1.4 GB of VRAM for the generator and reranker.
    # Ingestion embeds through its own path and is unaffected.
    embedding_num_gpu: int = 0
    # caps generated tokens; the single biggest CPU-side latency lever
    llm_num_predict: int = 180
    rewrite_num_predict: int = 512

    # generation http client (streaming keeps the connection alive between tokens,
    # so read_timeout only needs to cover the gap between chunks, not the full reply)
    generation_connect_timeout_seconds: float = 5.0
    generation_read_timeout_seconds: float = 180.0

    # openai-compatible providers (e.g. OpenAI, OpenRouter, LiteLLM)
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o-mini"

    # anthropic / claude
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_api_key: str = ""
    anthropic_llm_model: str = "claude-3-5-sonnet-20241022"

    # huggingface tei (sparse / SPLADE)
    tei_endpoint: str = "http://localhost:7100"
    tei_model: str = "naver/splade-v3"
    hf_token: str = ""

    # retrieval
    retrieval_top_k: int = 50            # candidates fetched per search before reranking
    rerank_top_n: int = 8                # chunks kept after reranking and put in the prompt
    rerank_provider: str = "none"        # none = keep fused order; anything else = Qwen3 reranker
    rerank_model: str = "Qwen/Qwen3-Reranker-0.6B"
    # pairs per reranker forward pass; bounds GPU activation memory (scores unchanged)
    rerank_batch_size: int = 5
    # Qwen3 reranker only: drop chunks whose relevance probability is below this
    # (the best chunk is always kept). 0 disables. Off by default: on the sample
    # alarms off-topic chunks scored 0.6-0.95 (same topic, wrong task) while a gold
    # chunk for am.nc.0004 scored <=0.10, so 0.2 dropped the wrong ones.
    rerank_min_score: float = 0.0
    rrf_k: int = 60  # reciprocal-rank-fusion constant; higher flattens rank differences

    # embeddings (the dims must match the vector/sparsevec columns in migration 0001)
    embedding_setup: str = "unified"  # unified (dense-only) or dual (dense + sparse)
    lexical_dim: int = 30522          # sparse vocab size (SPLADE / BERT wordpiece)
    semantic_dim: int = 1024          # qwen3-embedding:0.6b output size

    # langfuse
    langfuse_host: str = "http://langfuse:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # alarms data
    alarm_delim: str = "."  # separator in alarm codes: <origin>.<module>.<sequence>

    # query rewriting: how many domain keywords to look up for the query itself and
    # for the conversation context (retrieval/rewriter.py)
    KEYWORD_K: int = 10
    CONTEXT_K: int = 10

    # effort tier configurations
    LOW_CONFIG: dict = {
        "retrieval_k": 5,
        "reranker_n": 5,
        "context_k": 0,
        "reranker": "identity",
        "num_predict": 120,
        "num_rewrite": 0,
        "rewrite": False,
        "thinking": False
    }
    MID_CONFIG: dict = { # mid config is based on default settings
        "retrieval_k": 50,
        "reranker_n": 8,
        "context_k": 10,
        "reranker": "qwen3",
        "num_predict": 180,
        "num_rewrite": 256,
        "rewrite": True,
        "thinking": False
    }
    HIGH_CONFIG: dict = {
        "retrieval_k": 80,
        "reranker_n": 20,
        "context_k": 15,
        "reranker": "qwen3",
        "num_predict": 250,
        "num_rewrite": 512,
        "rewrite": True,
        "thinking": True
    }

    
    @model_validator(mode="after")
    def _require_explicit_allowed_hosts_outside_local(self) -> Self:
        """A deployment that accepts any Host can be used to forge links back to itself."""
        if self.app_env != "local" and "*" in self.allowed_hosts:
            raise ValueError(
                "ALLOWED_HOSTS must name the hostnames this service answers on "
                "(including the one the container health check uses) when APP_ENV is not local"
            )
        return self

    @model_validator(mode="after")
    def _reject_placeholder_secret_outside_local(self) -> Self:
        """The default secret is public (it's in this file), so tokens signed with it can be forged."""
        if self.app_env != "local" and (
            self.jwt_secret == LOCAL_JWT_SECRET or len(self.jwt_secret) < 32
        ):
            raise ValueError(
                "JWT_SECRET must be a random value of at least 32 characters "
                "when APP_ENV is not local"
            )
        return self

    @model_validator(mode="after")
    def _reject_placeholder_postgres_password_outside_local(self) -> Self:
        if self.app_env != "local" and self.postgres_password.strip().lower() in {
            "",
            "rag",
            "change_in_prod",
        }:
            raise ValueError(
                "POSTGRES_PASSWORD must be set to a non-placeholder value "
                "when APP_ENV is not local"
            )
        return self

    @property
    def postgres_dsn(self) -> str:
        """libpq URL for psycopg; migrations/env.py adapts it for SQLAlchemy."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """The process-wide Settings, read once. Tests that change env vars must call
    get_settings.cache_clear() for the change to take effect."""
    return Settings()