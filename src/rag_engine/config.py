"""Typed configuration loaded from environment (pydantic-settings).

Onboarding note:
- this file is the source of truth for runtime provider selection
- keep provider names and URLs here; do not hard-code model endpoints elsewhere
- required follow-up work: wire the selected provider into real embedding and
  generation adapters, then validate against Postgres + BM25 + Redis in a local
  docker stack
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    # auth
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60

    # postgres
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "rag"
    postgres_user: str = "rag"
    postgres_password: str = "rag"

    # redis
    redis_host: str = "redis"
    redis_port: int = 6379

    # provider selection
    embedding_provider: str = "ollama"
    lexical_provider: str = "bm25"
    llm_provider: str = "ollama"

    # ollama
    ollama_base_url: str = "http://ollama:11434"
    embedding_model: str = "qwen3-embedding:0.6b"
    llm_model: str = "qwen3:4b"

    # openai-compatible providers (e.g. OpenAI, OpenRouter, LiteLLM)
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o-mini"

    # anthropic / claude
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_api_key: str = ""
    anthropic_llm_model: str = "claude-3-5-sonnet-20241022"

    # retrieval
    retrieval_top_k: int = 50
    rerank_top_n: int = 8
    rrf_k: int = 60
    bm25_index_dir: str = "/var/lib/rag/bm25"

    # embeddings
    embedding_setup: str = "unified" # unified or dual
    dense_n: int = 1024
    sparse_n: int = 250002

    # langfuse
    langfuse_host: str = "http://langfuse:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
