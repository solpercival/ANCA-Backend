"""HTTP surface: health, resolve-by-code, and conversational chat."""
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from rag_engine.api.auth import Principal, Tier, current_principal
from rag_engine.api.errors import RetrievalUnavailable
from rag_engine.api.rate_limit import rate_limit_dependency
from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    ResolveRequest,
    ResolveResponse,
)
from rag_engine.config import get_settings
from rag_engine.orchestrator import Orchestrator, get_orchestrator

router = APIRouter()
settings = get_settings()
resolve_rate_limit = rate_limit_dependency(
    "resolve", "resolve_rate_limit_per_ip", "resolve_rate_limit_per_tier"
)
chat_rate_limit = rate_limit_dependency(
    "chat", "chat_rate_limit_per_ip", "chat_rate_limit_per_tier"
)

def get_orchestrator_from_request(request: Request):
    orch = getattr(request.app.state, "orchestrator", None)
    if orch is None:
        try:
            orch = get_orchestrator()
            request.app.state.orchestrator = orch
        except Exception as exc:  # placeholder runtime: DB/provider wiring still pending
            raise RetrievalUnavailable(
                "Orchestrator is not available yet; DB and retrieval backends are still being wired in."
            ) from exc
    return orch


@router.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", tags=["ops"])
async def ready(request: Request) -> dict[str, object]:
    checks = {
        "postgres": False,
        "redis": False,
        "model_server": False,
    }

    pg_pool = getattr(request.app.state, "pg_pool", None)
    if pg_pool is not None:
        try:
            async with pg_pool.connection() as conn:
                await conn.execute("SELECT 1")
            checks["postgres"] = True
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

    raise HTTPException(
        status_code=503,
        detail={"status": "not_ready", "checks": checks},
    )


@router.post("/api/v1/resolve", response_model=ResolveResponse, tags=["resolve"])
async def resolve(
    req: ResolveRequest,
    principal: Principal = Depends(current_principal),
    _: None = Depends(resolve_rate_limit),
    orch: Orchestrator = Depends(get_orchestrator),
) -> ResolveResponse:
    resp = await orch.resolve(req, tier=principal.tier)
    # Tier gate: only technician/partner see likely_causes.
    if principal.tier == Tier.operator:
        resp.likely_causes = []
    return resp


@router.post("/api/v1/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    req: ChatRequest,
    principal: Principal = Depends(current_principal),
    _: None = Depends(chat_rate_limit),
    orch: Orchestrator = Depends(get_orchestrator),
) -> ChatResponse:
    return await orch.chat(req, tier=principal.tier)
