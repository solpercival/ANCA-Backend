"""Typed configuration loaded from environment (pydantic-settings)."""
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

    # model servers
    embedding_base_url: str = "http://embedding-server:8000/v1"
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    reranker_base_url: str = "http://embedding-server:8000/v1"
    reranker_model: str = "Qwen/Qwen3-Reranker-0.6B"
    llm_base_url: str = "http://response-server:8000/v1"
    llm_model: str = "Qwen/Qwen3-4B-Instruct"

    # retrieval
    retrieval_top_k: int = 50
    rerank_top_n: int = 8
    rrf_k: int = 60

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
