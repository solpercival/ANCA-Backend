"""HTTP surface under /api/v2: health/readiness probes, resolve-by-code, and chat.

Every business endpoint authenticates (current_principal / require), is rate
limited per IP and per tier, and gets the shared Orchestrator from
get_orchestrator. Tier-based visibility rules are applied here, after the
orchestrator returns, so access never depends on what generation produced.
"""

import asyncio

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from rag_engine.api.errors import RetrievalUnavailable
from rag_engine.api.rate_limit import rate_limit_dependency
from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    ResolveRequest,
    ResolveResponse,
)
from rag_engine.auth.dependencies import current_principal, require
from rag_engine.auth.tiers import Principal, can_use_chat, can_view_likely_causes
from rag_engine.config import get_settings
from rag_engine.orchestrator import Orchestrator, get_orchestrator

router = APIRouter(prefix="/api/v2", tags=["api"])
settings = get_settings()
resolve_rate_limit = rate_limit_dependency(
    "resolve", "resolve_rate_limit_per_ip", "resolve_rate_limit_per_tier"
)
chat_rate_limit = rate_limit_dependency(
    "chat", "chat_rate_limit_per_ip", "chat_rate_limit_per_tier"
)


def get_orchestrator_from_request(request: Request):
    """Orchestrator cached on app.state, built on first use.

    Not used by the routes below (they depend on get_orchestrator directly); kept
    for callers that need a 503 instead of a crash while backends are unwired.
    """
    orch = getattr(request.app.state, "orchestrator", None)
    if orch is None:
        try:
            orch = get_orchestrator()
            request.app.state.orchestrator = orch
        except Exception as exc:  # placeholder runtime: DB/provider wiring still pending
            raise RetrievalUnavailable(
                "Orchestrator is not available yet; "
                "DB and retrieval backends are still being wired in."
            ) from exc
    return orch


def _ping_postgres(pool) -> bool:
    # bounded wait so an exhausted pool or unreachable DB fails the check instead of hanging
    with pool.connection(timeout=3.0) as conn:
        return conn.execute("SELECT 1").fetchone() is not None


@router.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness: the process is up. Touches no dependencies."""
    return {"status": "ok"}


# response_model=None: FastAPI can't build a response model from a return type that
# includes a Response class, and raises at import time (the app would not start)
@router.get("/ready", tags=["ops"], response_model=None)
async def ready(request: Request) -> dict[str, object] | JSONResponse:
    """Readiness: Postgres, Redis and the model server all answer.

    200 with the per-dependency checks when all pass, otherwise 503 with the same
    checks so the failing one is visible.
    Each probe has a short timeout.
    The 503 is a JSONResponse so the
    error handler does not stringify the checks body.
    """
    checks = {
        "postgres": False,
        "redis": False,
        "model_server": False,
    }

    # Postgres: the pool is sync (psycopg_pool.ConnectionPool), so probe it off the event loop
    pg_pool = getattr(request.app.state, "pg_pool", None)
    if pg_pool is not None:
        try:
            checks["postgres"] = await asyncio.to_thread(_ping_postgres, pg_pool)
        except Exception:
            checks["postgres"] = False

    # Redis
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is not None:
        try:
            checks["redis"] = await redis_client.ping()
        except Exception:
            checks["redis"] = False

    # Model server (Ollama/OpenAI-compatible endpoint)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            checks["model_server"] = resp.status_code == 200
    except Exception:
        checks["model_server"] = False

    if all(checks.values()):
        return {"status": "ok", "checks": checks}

    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "checks": checks},
    )


@router.post("/resolve", response_model=ResolveResponse, tags=["resolve"])
async def resolve(
    req: ResolveRequest,
    principal: Principal = Depends(current_principal),
    _: None = Depends(resolve_rate_limit),
    orch: Orchestrator = Depends(get_orchestrator),
) -> ResolveResponse:
    """Troubleshooting guidance for one alarm code, grounded in the documentation.

    Errors: 404 unknown_alarm_code, 429 rate_limited, 503 retrieval/model unavailable.
    """
    resp = await orch.resolve(req, tier=principal.tier)
    # Tier rules are applied here rather than in the orchestrator, so access never
    # depends on what generation happened to return.
    if not can_view_likely_causes(principal.tier):
        resp.likely_causes = []
    resp.ai_chat_available = can_use_chat(principal.tier)
    return resp


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    req: ChatRequest,
    principal: Principal = Depends(require(can_use_chat)),
    _: None = Depends(chat_rate_limit),
    orch: Orchestrator = Depends(get_orchestrator),
) -> ChatResponse:
    """Free-text follow-up question within a conversation (tiers allowed by can_use_chat)."""
    return await orch.chat(req, tier=principal.tier)
