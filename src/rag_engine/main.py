"""FastAPI application entrypoint."""
import logging
import uuid
from contextlib import asynccontextmanager

import httpx
import redis.asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from rag_engine.api.error_handlers import register_error_handlers
from rag_engine.api.routes import router
from rag_engine.config import get_settings
from rag_engine.orchestrator import get_orchestrator

settings = get_settings()
logging.basicConfig(level=settings.log_level)
log = logging.getLogger("rag_engine.main")


async def create_postgres_pool():
    """Placeholder for later Postgres integration."""
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    try:
        app.state.orchestrator = get_orchestrator()
    except Exception:
        app.state.orchestrator = None
        log.warning("Orchestrator runtime not ready; keeping placeholder app state until DB/provider wiring lands.", exc_info=True)

    app.state.httpx_client = httpx.AsyncClient(timeout=120.0)

    try:
        app.state.pg_pool = await create_postgres_pool()
    except Exception:
        app.state.pg_pool = None
        log.warning("Postgres pool not initialized yet; placeholder only.", exc_info=True)

    try:
        app.state.redis = redis.asyncio.Redis.from_url("redis://redis:6379/0")
    except Exception:
        app.state.redis = None
        log.warning("Redis connection not initialized yet; placeholder only.", exc_info=True)

    yield

    # shutdown
    if getattr(app.state, "httpx_client", None) is not None:
        await app.state.httpx_client.aclose()
    if getattr(app.state, "redis", None) is not None:
        await app.state.redis.aclose()
    if getattr(app.state, "pg_pool", None) is not None:
        await app.state.pg_pool.close()

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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

def get_httpx_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.httpx_client

def get_embedder(request: Request):
    client = request.app.state.httpx_client
    return get_embedding_backend(client)

def get_generator(request: Request):
    client = request.app.state.httpx_client
    return get_generation_backend(client)

@app.get("/", tags=["ops"])
async def root() -> dict[str, str]:
    return {"service": "rag-engine", "env": settings.app_env}