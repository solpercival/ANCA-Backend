"""HTTP surface under API_PREFIX (/api/<version>): health/readiness probes,
resolve-by-code, chat, and feedback on chat replies.

Every business endpoint identifies the caller (optional_principal on /resolve and
/feedback, which with ALLOW_ANONYMOUS_OPERATOR admits a caller with no token as an
operator; require on /chat), is rate limited per IP and per tier, and gets the
shared Orchestrator from get_orchestrator. Tier-based visibility rules are applied here, after the
orchestrator returns, so access never depends on what generation produced.
"""

import asyncio

import httpx
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse

from rag_engine.api.errors import NotFound
from rag_engine.api.rate_limit import rate_limit_dependency
from rag_engine.api.safety import is_safety_alarm
from rag_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    ResolveRequest,
    ResolveResponse,
)
from rag_engine.auth.dependencies import optional_principal, require
from rag_engine.auth.tiers import (
    Principal,
    can_use_chat,
    can_view_likely_causes,
    should_escalate_when_unsure,
)
from rag_engine.config import API_PREFIX, get_settings
from rag_engine.orchestrator import Orchestrator, get_orchestrator

router = APIRouter(prefix=API_PREFIX, tags=["api"])
settings = get_settings()
resolve_rate_limit = rate_limit_dependency(
    "resolve",
    "resolve_rate_limit_per_ip",
    "resolve_rate_limit_per_tier",
    principal_dependency=optional_principal,
)
feedback_rate_limit = rate_limit_dependency(
    "feedback",
    "feedback_rate_limit_per_ip",
    "feedback_rate_limit_per_tier",
    principal_dependency=optional_principal,
)
chat_rate_limit = rate_limit_dependency(
    "chat", "chat_rate_limit_per_ip", "chat_rate_limit_per_tier"
)

# Shown to operators with escalation_suggested; kept out of `steps`, which hold
# only doc-grounded guidance.
ESCALATION_NOTE = "If you are unsure, stop and escalate to a technician before acting."
# doc_coverage values that leave an operator without a complete, documented fix
_ESCALATE_COVERAGE = frozenset({"none", "partial"})


def _set_server_timing(response: Response, timings: dict[str, float]) -> None:
    """Send the answer's stage timings as a Server-Timing header (milliseconds), e.g.
    `retrieve;dur=187.6, rerank;dur=402.1, generate;dur=1310.4, total;dur=1900.1`.
    Browser devtools show it per request, and the front end can read it through
    PerformanceResourceTiming.serverTiming. Nothing is sent when the answer was decided
    without the pipeline (an early "not covered")."""
    if timings:
        response.headers["Server-Timing"] = ", ".join(
            f"{stage};dur={seconds * 1000:.1f}" for stage, seconds in timings.items()
        )


def _ping_postgres(pool) -> bool:
    """Whether Postgres answers a trivial query (blocking). The wait for a connection
    is bounded, so an exhausted pool or unreachable DB fails the check instead of
    hanging."""
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
    response: Response,
    principal: Principal = Depends(optional_principal),
    _: None = Depends(resolve_rate_limit),
    orch: Orchestrator = Depends(get_orchestrator),
) -> ResolveResponse:
    """Troubleshooting guidance for one alarm code, grounded in the documentation.

    Open to every tier, and to callers with no token (as an operator) when
    ALLOW_ANONYMOUS_OPERATOR is on.
    Errors: 404 unknown_alarm_code, 429 rate_limited, 503 retrieval/model unavailable.
    """
    resp = await orch.resolve(req, tier=principal.tier)
    _set_server_timing(response, resp._stage_timings)
    # Tier rules are applied here rather than in the orchestrator, so access never
    # depends on what generation happened to return.
    if not can_view_likely_causes(principal.tier):
        resp.likely_causes = []
    resp.ai_chat_available = can_use_chat(principal.tier)
    # Operators are told to escalate instead of acting alone on an alarm that is
    # safety-related or that the docs don't fully cover. Decided from the alarm's
    # severity and the coverage, never from what the orchestrator put in the notes.
    # ESCALATION_SUGGESTION_ENABLED=false turns the suggestion off entirely
    resp.escalation_suggested = (
        settings.escalation_suggestion_enabled
        and should_escalate_when_unsure(principal.tier)
        and (is_safety_alarm(resp.severity_category) or resp.doc_coverage in _ESCALATE_COVERAGE)
    )
    resp.escalation_note = ESCALATION_NOTE if resp.escalation_suggested else None
    return resp


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    req: ChatRequest,
    response: Response,
    principal: Principal = Depends(require(can_use_chat)),
    _: None = Depends(chat_rate_limit),
    orch: Orchestrator = Depends(get_orchestrator),
) -> ChatResponse:
    """Free-text follow-up question within a conversation (tiers allowed by can_use_chat)."""
    resp = await orch.chat(req, tier=principal.tier)
    _set_server_timing(response, resp._stage_timings)
    return resp


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT, tags=["chat"])
async def feedback(
    req: FeedbackRequest,
    principal: Principal = Depends(optional_principal),
    _: None = Depends(feedback_rate_limit),
    orch: Orchestrator = Depends(get_orchestrator),
) -> None:
    """Mark a reply (by the response_id /chat or /resolve returned) as having helped
    or not. Open to every tier, and to anonymous operators like /resolve.

    Sending it again overwrites the earlier value. The next chat turn in the
    conversation passes it to the query rewriter.
    Errors: 404 not_found (no such reply in the conversation), 429 rate_limited.
    """
    if not await orch.record_feedback(req.conversation_id, req.response_id, req.helpful):
        raise NotFound("No such response in this conversation")
