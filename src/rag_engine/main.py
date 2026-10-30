"""FastAPI application entrypoint (`uvicorn rag_engine.main:app`).

Startup (lifespan) builds the shared HTTP client, the orchestrator, and the
Postgres/Redis pools. It degrades instead of crashing: if storage isn't reachable
the app still starts, auth storage is marked unavailable, and <API_PREFIX>/ready
reports which dependency is down.

Request path, outermost first: host check -> security headers -> gzip -> CORS ->
request-id/body-size middleware -> routes. The schema itself comes from the Alembic
migrations (the `migrate` compose service), not from this process.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from rag_engine.api.error_handlers import _json, register_error_handlers
from rag_engine.api.errors import ErrorBody, ErrorCode
from rag_engine.api.routes import router
from rag_engine.api.security import add_security_middleware
from rag_engine.auth.routes import router as auth_router
from rag_engine.auth.session_store import RedisSessionStore
from rag_engine.auth.user_repository import PostgresUserRepository, ensure_auth_schema
from rag_engine.config import API_PREFIX, get_settings
from rag_engine.orchestrator import get_orchestrator
from rag_engine.stores.cache import close_cache_pool, get_cache_client, init_cache_pool
from rag_engine.stores.db import close_db_pool, get_db_pool, init_db_pool

settings = get_settings()
logging.basicConfig(level=settings.log_level)
log = logging.getLogger("rag_engine.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build shared resources on app.state at startup and close them at shutdown.

    Sets httpx_client, orchestrator, user_repository, session_store, pg_pool and
    redis. A failure to build the orchestrator or reach storage is logged, not
    raised: the matching state is left as None and requests that need it get a 503.
    """
    # startup
    # generous read timeout: generation streams token-by-token, so this only bounds
    # the gap between chunks, not the total time a slow reply can take
    app.state.httpx_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=settings.generation_connect_timeout_seconds,
            read=settings.generation_read_timeout_seconds,
            write=10.0,
            pool=5.0,
        )
    )

    try:
        app.state.orchestrator = get_orchestrator()
    except Exception:
        app.state.orchestrator = None
        log.warning(
            "Orchestrator runtime not ready; keeping placeholder app state until "
            "DB/provider wiring lands.",
            exc_info=True,
        )

    storage_ready = False
    try:
        init_db_pool()
        init_cache_pool()
        ensure_auth_schema()  # idempotent auth-table patch for pre-migration databases
        storage_ready = True
    except Exception:
        log.warning("Storage pools not initialized; auth storage is unavailable.", exc_info=True)

    app.state.user_repository = PostgresUserRepository() if storage_ready else None
    app.state.session_store = RedisSessionStore()
    app.state.pg_pool = get_db_pool()
    app.state.redis = get_cache_client()

    yield

    # shutdown
    if getattr(app.state, "httpx_client", None) is not None:
        await app.state.httpx_client.aclose()
    await close_cache_pool()
    close_db_pool()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Tag each request with an id, cap API body size, and write one access log line.

    The id is the caller's X-Request-ID if sent, else a new one; it is echoed in the
    response header and in error bodies. For API routes, bodies over
    max_request_body_bytes get 413 -- checked on Content-Length first, then on the
    actual body, since the header can be absent or wrong.
    """
    request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request_id = request.state.request_id
    t0 = time.perf_counter()

    if request.url.path.startswith(API_PREFIX):
        content_length = request.headers.get("content-length")
        try:
            declared_length = int(content_length) if content_length else None
        except ValueError:
            declared_length = None

        if declared_length is not None and declared_length > settings.max_request_body_bytes:
            return _json(
                413,
                ErrorBody(
                    code=ErrorCode.payload_too_large,
                    message="Request body exceeds the configured size limit.",
                    request_id=request.state.request_id,
                ),
            )

        body = await request.body()
        if len(body) > settings.max_request_body_bytes:
            return _json(
                413,
                ErrorBody(
                    code=ErrorCode.payload_too_large,
                    message="Request body exceeds the configured size limit.",
                    request_id=request.state.request_id,
                ),
            )

    response = await call_next(request)
    latency_ms = (time.perf_counter() - t0) * 1000

    response.headers["x-request-id"] = request_id

    log.info(
        "access request_id=%s method=%s path=%s status=%s latency_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        latency_ms,
    )
    return response


register_error_handlers(app)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_security_middleware(app, settings)
app.include_router(router)
app.include_router(auth_router)


def get_httpx_client(request: Request) -> httpx.AsyncClient:
    """FastAPI dependency: the shared outbound HTTP client created at startup."""
    return request.app.state.httpx_client


@app.get("/", tags=["ops"])
async def root() -> dict[str, str]:
    """Service name and environment."""
    return {"service": "rag-engine", "env": settings.app_env}
