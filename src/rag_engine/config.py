"""Typed configuration loaded from environment (pydantic-settings).

Onboarding note:
- this file is the source of truth for runtime provider selection
- keep provider names and URLs here; do not hard-code model endpoints elsewhere
- required follow-up work: wire the selected provider into real embedding and
  generation adapters, then validate against Postgres + Redis in a local
  docker stack
"""
from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_JWT_SECRET = "change-me-in-prod"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    # auth
    jwt_secret: str = LOCAL_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "anca-rag-engine"
    jwt_audience: str = "anca-frontend"
    access_token_ttl_minutes: int = 15
    refresh_token_idle_days: int = 7
    session_max_days: int = 30
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

    # redis
    redis_host: str = "redis"
    redis_port: int = 6379

    # provider selection
    embedding_provider: str = "ollama"
    lexical_provider: str = "postgres"
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
    rerank_provider: str = "none"
    rerank_model: str = "Qwen/Qwen3-Reranker-0.6B"
    rrf_k: int = 60

    # langfuse
    langfuse_host: str = "http://langfuse:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    @model_validator(mode="after")
    def _reject_placeholder_secret_outside_local(self) -> Self:
        if self.app_env != "local" and (
            self.jwt_secret == LOCAL_JWT_SECRET or len(self.jwt_secret) < 32
        ):
            raise ValueError(
                "JWT_SECRET must be a random value of at least 32 characters "
                "when APP_ENV is not local"
            )
        return self

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
