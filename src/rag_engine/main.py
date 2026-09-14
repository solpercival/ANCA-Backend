"""FastAPI application entrypoint."""
import logging
import httpx
import redis.asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

from contextlib import asynccontextmanager

from rag_engine.api.routes import router
from rag_engine.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup 
    app.state.httpx_client = httpx.AsyncClient(timeout=120.0)
    app.state.pg_pool = await create_postgres_pool()
    app.state.redis = redis.asyncio.Redis.from_url(...)
    app.state.bm25_index = load_bm25_index_once()
    
    yield

    #shutdown
    await app.state.httpx_client.aclose()
    await app.state.redis.aclose()
    await app.state.pg_pool.close()
    app.state.bm25_index.close()

app = FastAPI(lifespan=lifespan, title="CNC Troubleshooting RAG Engine", version="0.1.0")
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

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", tags=["ops"])
async def root() -> dict[str, str]:
    return {"service": "rag-engine", "env": settings.app_env}