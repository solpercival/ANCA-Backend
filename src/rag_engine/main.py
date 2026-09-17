"""FastAPI application entrypoint."""
import logging
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from rag_engine.api.error_handlers import register_error_handlers
from rag_engine.api.routes import router
from rag_engine.auth.routes import router as auth_router
from rag_engine.auth.session_store import RedisSessionStore
from rag_engine.config import get_settings
from rag_engine.orchestrator import get_orchestrator
from rag_engine.stores.cache import close_cache_pool, init_cache_pool
from rag_engine.stores.db import close_db_pool, init_db_pool

settings = get_settings()
logging.basicConfig(level=settings.log_level)
log = logging.getLogger("rag_engine.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.httpx_client = httpx.AsyncClient(timeout=120.0)

    try:
        app.state.orchestrator = get_orchestrator()
    except Exception:
        app.state.orchestrator = None
        log.warning(
            "Orchestrator runtime not ready; keeping placeholder app state until "
            "DB/provider wiring lands.",
            exc_info=True,
        )

    try:
        init_db_pool()
        init_cache_pool()
    except Exception:
        log.warning("Storage pools not initialized; auth storage is unavailable.", exc_info=True)

    # Attach the Postgres UserRepository here once the datamapper lands.
    app.state.user_repository = None
    app.state.session_store = RedisSessionStore()

    yield

    # shutdown
    if getattr(app.state, "httpx_client", None) is not None:
        await app.state.httpx_client.aclose()
    close_cache_pool()
    close_db_pool()

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


register_error_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(auth_router)

def get_httpx_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.httpx_client

@app.get("/", tags=["ops"])
async def root() -> dict[str, str]:
    return {"service": "rag-engine", "env": settings.app_env}