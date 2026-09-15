"""HTTP surface: health, resolve-by-code, and conversational chat."""
from fastapi import APIRouter, Depends, Request

from rag_engine.api.auth import Principal, Tier, current_principal
from rag_engine.api.errors import RetrievalUnavailable
from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    ResolveRequest,
    ResolveResponse,
)
from rag_engine.orchestrator import Orchestrator, get_orchestrator

router = APIRouter()

def get_orchestrator_from_request(request: Request):
    orch = getattr(request.app.state, "orchestrator", None)
    if orch is None:
        try:
            orch = get_orchestrator()
            request.app.state.orchestrator = orch
        except Exception as exc:  # placeholder runtime: DB/provider wiring still pending
            raise RetrievalUnavailable(
                "Orchestrator is not available yet; the DB and retrieval backends are still being wired in."
            ) from exc
    return orch


@router.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/resolve", response_model=ResolveResponse, tags=["resolve"])
async def resolve(
    req: ResolveRequest,
    principal: Principal = Depends(current_principal),
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
    orch: Orchestrator = Depends(get_orchestrator),
) -> ChatResponse:
    return await orch.chat(req, tier=principal.tier)
