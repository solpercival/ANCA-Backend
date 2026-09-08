"""FastAPI application entrypoint."""
import logging

from fastapi import FastAPI

from rag_engine.api.routes import router
from rag_engine.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(title="CNC Troubleshooting RAG Engine", version="0.1.0")
app.include_router(router)


@app.get("/", tags=["ops"])
async def root() -> dict[str, str]:
    return {"service": "rag-engine", "env": settings.app_env}
