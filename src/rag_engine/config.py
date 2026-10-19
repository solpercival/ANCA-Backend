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

# The API version lives here and nowhere else: routers, the refresh-cookie path, the
# body-size check, scripts and tests all read API_PREFIX. A constant rather than a
# setting, because the version is part of the contract with the frontend, not
# something a deployment may change.
API_VERSION = "v2"
API_PREFIX = f"/api/{API_VERSION}"


class Settings(BaseSettings):
    """All runtime settings. Each field is read from the environment variable of the
    same name (case-insensitive, e.g. POSTGRES_HOST), then from .env, then this
    default. Outside APP_ENV=local, the validators below refuse unsafe defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    allowed_hosts: list[str] = ["*"]  # must be named explicitly outside local
    gzip_minimum_size: int = 500  # bytes
    hsts_max_age: int = 63072000  # two years, the value HSTS preload lists expect

    # auth
    jwt_secret: str = LOCAL_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "anca-rag-engine"
    jwt_audience: str = "anca-frontend"
    access_token_ttl_minutes: int = 15  # bearer JWT lifetime
    refresh_token_idle_days: int = 7  # session ends if unused this long
    session_max_days: int = 30  # absolute session cap, however active
    auth_cookie_secure: bool = True
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    login_max_attempts: int = 5
    login_max_attempts_per_ip: int = 20
    login_window_seconds: int = 900
    cors_allow_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ]
    # /resolve and /feedback without a bearer token answer as an operator (the
    # narrowest tier). A token that is sent must still be valid; /chat always needs one
    allow_anonymous_operator: bool = False
    escalation_suggestion_enabled: bool = True

    # postgres
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "rag"
    postgres_user: str = "rag"
    postgres_password: str = "rag"

    # redis (sessions, rate limits, and the generated-answer cache below)
    redis_host: str = "redis"
    redis_port: int = 6379
    # Reuse a generated resolve answer when the same prompt is sent to the same
    # model again (RedisConnection in stores/search.py). The key covers the whole
    # prompt, so a change to the docs, the retrieval, the alarm or the instructions
    # is a different entry; retrieval and reranking still run on every request. Off
    # by default: it hides the run-to-run variation the eval measures.
    response_cache_enabled: bool = False
    response_prefix: str = "response:"
    response_ttl: int = 86400  # seconds an answer is kept

    # rate limiting: requests per window, per client IP and per account tier
    rate_limit_window_seconds: int = 60
    resolve_rate_limit_per_ip: int = 30
    resolve_rate_limit_per_tier: int = 120
    chat_rate_limit_per_ip: int = 10
    chat_rate_limit_per_tier: int = 60
    feedback_rate_limit_per_ip: int = 30
    feedback_rate_limit_per_tier: int = 120
    max_request_body_bytes: int = 64 * 1024

    # provider selection: which backend implements each interface (see providers.py
    # and orchestrator.get_orchestrator for the accepted names)
    dense_embedding_provider: str = "ollama"
    sparse_embedding_provider: str = "huggingface_tei"
    lexical_provider: str = "postgres"
    llm_provider: str = "ollama"
    chat_store_provider: str = "postgres"

    # ollama
    ollama_base_url: str = "http://ollama:11434"
    embedding_model: str = "qwen3-embedding:0.6b"
    # qwen3:8b honours think:false, and on the eval gave more complete fixes than the
    # 4B instruct build (fix_present 0.909 against 0.727) at the same speed on a 12 GB
    # card. Needs about 6 GB of GPU memory; on a smaller card use
    # qwen3:4b-instruct-2507-q4_K_M (not plain qwen3:4b, the always-thinking 2507
    # model, which ignores think:false and spends num_predict on reasoning text)
    llm_model: str = "qwen3:8b"
    # model that rewrites a follow-up chat message into a standalone query
    # (retrieval/rewriter.py). Empty = LLM_MODEL, which is already loaded. A much
    # smaller model does not do the task: qwen3:0.6b returned "why does it happen?"
    # unchanged, with commentary around it.
    rewrite_model: str = ""
    # query-time embedding context. Ollama's default (4096) makes the 0.6B embedder
    # hold ~2.4 GB of VRAM; queries are short, and 1024 still covers the longest chat
    # message (4096 chars ~ 1k tokens). Longer input is truncated, not rejected.
    embedding_num_ctx: int = 1024
    # layers of the query embedder Ollama puts on the GPU; 0 = CPU. One short query per
    # request is cheap on CPU and frees ~1.4 GB of VRAM for the generator and reranker.
    # Ingestion embeds through its own path and is unaffected.
    embedding_num_gpu: int = 0
    # caps generated tokens at the default (medium) effort; the single biggest
    # CPU-side latency lever
    llm_num_predict: int = 180
    # sampling temperature for answer generation. 0 = always the most likely token, so
    # the same alarm and context give the same steps: grounded answers don't benefit
    # from variety, and bench/eval runs become comparable (Ollama's own default, 0.8,
    # moved fix_present by a whole alarm between identical runs)
    llm_temperature: float = 0.0
    # caps the query rewrite's output tokens at the default (medium) effort
    rewrite_num_predict: int = 256

    # Make answers repeatable: temperature 0 and a fixed seed.
    # On for resolve, so the same alarm gets the same steps.
    # Off for chat, so conversations keep some variety.
    resolve_deterministic: bool = True
    chat_deterministic: bool = False
    deterministic_temperature: float = 0.0
    deterministic_seed: int = 42

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
    # both apply to the default (medium) effort; low and high have fixed presets below
    retrieval_top_k: int = 50  # candidates fetched per search before reranking
    rerank_top_n: int = 8  # chunks kept after reranking and put in the prompt
    rerank_provider: str = "none"  # none = keep fused order; anything else = Qwen3 reranker
    rerank_model: str = "Qwen/Qwen3-Reranker-0.6B"
    # pairs per reranker forward pass; bounds GPU activation memory (scores unchanged)
    rerank_batch_size: int = 5
    # Qwen3 reranker only: tokens per instruction+query+chunk pair; a longer chunk is
    # cut off and scored on its beginning alone. At 512 a long table was judged by its
    # header rows: an off-topic 886-token parameter table scored 0.40 for a firmware
    # alarm and 0.00 once read in full. 2048 covers all but a handful of chunks; lower
    # it to save GPU memory (about +0.5 GB over 512 when a batch holds a long chunk).
    rerank_max_length: int = 2048
    # Qwen3 reranker only: drop chunks whose relevance probability is below this
    # (the best chunk is always kept). 0 disables. Off by default: on the sample
    # alarms off-topic chunks scored 0.6-0.95 (same topic, wrong task) while a gold
    # chunk for am.nc.0004 scored <=0.10, so 0.2 dropped the wrong ones.
    rerank_min_score: float = 0.0
    # Qwen3 reranker only: a cutoff relative to the query's best chunk. Beyond the
    # first rerank_min_keep chunks, a chunk is kept only if it also scores at least
    # this fraction of the top score. The absolute floor above cannot separate the
    # two cases this does: a query whose best chunk is 0.93 and the rest 0.10 or
    # less (the rest is noise) and one whose chunks all score 0.7-0.96 (all kept).
    # 0 disables, leaving only rerank_min_score.
    rerank_relative_min: float = 0.0
    # Chunks always kept from the top of the ranking, whatever they score (at least
    # 1). 1 is the behaviour before the relative cutoff existed: only the best chunk
    # is guaranteed. 2 protects a second gold chunk that scores low in absolute
    # terms (am.nc.0004's scores about 0.10).
    rerank_min_keep: int = 1
    # Resolve context: a selected chunk is passed to the generator as its whole
    # section (every chunk under the same heading) when the section is at most this
    # many characters. Ingestion cuts a section into text, list, table and code
    # pieces, so a procedure's steps end up in different chunks and any one the
    # reranker cuts is a step lost. Larger sections (long reference tables) stay as
    # the single chunk. 0 disables.
    context_section_max_chars: int = 2500
    # ...and only while the whole context stays within this many characters, so the
    # prompt fits the generator's context window (about 3.3 characters per token).
    context_max_chars: int = 8000
    # diagnosis: keep each resolve's final prompt and context in Redis for a day
    # (debug:prompt:<code>, debug:context:<code>), read by eval/diagnose_gaps.py
    resolve_debug_prompt: bool = False
    # Relevance floor for a resolve answer: if even the best reranked chunk scores
    # below this P(yes), nothing retrieved is about the alarm, so the answer is "not
    # covered" without calling the generator (it would otherwise build steps out of
    # unrelated text). Unlike rerank_min_score this looks only at the best chunk.
    # 0 disables. Chosen from the sample alarms: answerable ones had a best score of
    # 0.47-0.99; an operator asking about User Guide-only alarms got 0.00-0.02.
    # Applies only with a reranker that scores relevance (Qwen3), so not at low effort.
    resolve_min_relevance: float = 0.1
    # Grounding floor for resolve steps: a step is dropped when less than this share
    # of its key words is found in the context the answer was generated from (or in
    # the alarm's own title and message, which the prompt also shows the model).
    # Catches steps the model invents. 0 disables.
    step_support_min: float = 0.0
    rrf_k: int = 60  # reciprocal-rank-fusion constant; higher flattens rank differences

    # embeddings (the dims must match the vector/sparsevec columns in migration 0001)
    embedding_setup: str = "unified"  # unified (dense-only) or dual (dense + sparse)
    lexical_dim: int = 30522  # sparse vocab size (SPLADE / BERT wordpiece)
    semantic_dim: int = 1024  # qwen3-embedding:0.6b output size

    # langfuse
    langfuse_host: str = "http://langfuse:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # alarms data
    alarm_delim: str = "."  # separator in alarm codes: <origin>.<module>.<sequence>

    # Alarm severity categories treated as safety-related: a resolve answer for one
    # carries a verify-before-acting note, and operators are told to escalate
    # (api/safety.py). Compared case-insensitively. Widen it as the client's
    # definition of "safety-related" grows, e.g.
    # SAFETY_SEVERITY_CATEGORIES='["Fatal","Critical"]'
    safety_severity_categories: set[str] = {"Fatal"}

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
        "thinking": False,
    }
    # retrieval_k, reranker_n, num_predict and num_rewrite here are overwritten from
    # RETRIEVAL_TOP_K, RERANK_TOP_N, LLM_NUM_PREDICT and REWRITE_NUM_PREDICT (see
    # _medium_effort_follows_settings), so those settings tune the default effort
    MID_CONFIG: dict = {
        "retrieval_k": 50,
        "reranker_n": 8,
        "context_k": 10,
        # resolve: the reranker reads the first 30 candidates, not 10. The embedding
        # search is the weaker judge: for am.cfg.0001 the right section sat at rank 25
        # behind short function-reference entries, so the reranker never saw it.
        "rerank_k": 30,
        "reranker": "qwen3",
        "num_predict": 180,
        "num_rewrite": 256,
        "rewrite": True,
        "thinking": False,
    }
    HIGH_CONFIG: dict = {
        "retrieval_k": 80,
        "reranker_n": 20,
        "context_k": 30,
        "reranker": "qwen3",
        "num_predict": 250,
        "num_rewrite": 512,
        "rewrite": True,
        # off: with thinking on, qwen3:8b spent all 250 tokens reasoning and every
        # high-effort resolve came back "not covered" (33 of 33 eval requests)
        "thinking": False,
    }

    @model_validator(mode="after")
    def _medium_effort_follows_settings(self) -> Self:
        """Medium is the default effort, so the documented knobs are its values."""
        self.MID_CONFIG = {
            **self.MID_CONFIG,
            "retrieval_k": self.retrieval_top_k,
            "reranker_n": self.rerank_top_n,
            "num_predict": self.llm_num_predict,
            "num_rewrite": self.rewrite_num_predict,
        }
        return self

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
        """The default secret is public (it's in this file), so tokens signed with it
        can be forged."""
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
        """The default and example passwords are public (they're in this repo), so a
        database left on one is open to anyone who can reach it."""
        if self.app_env != "local" and self.postgres_password.strip().lower() in {
            "",
            "rag",
            "change_in_prod",
        }:
            raise ValueError(
                "POSTGRES_PASSWORD must be set to a non-placeholder value when APP_ENV is not local"
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
