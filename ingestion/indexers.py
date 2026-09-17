"""Model-backed embedding plus PostgreSQL/pgvector."""
import json
from pathlib import Path

# ingestion/indexers.py
from rag_engine.providers import get_lexical_backend

import httpx
import psycopg
from pgvector.psycopg import register_vector

from ingestion.chunker import RawChunk
from rag_engine.config import get_settings


def _embed(chunks: list[RawChunk], client: httpx.Client) -> list[list[float]]:
    settings = get_settings()
    response = client.post(
        f"{settings.ollama_base_url.rstrip('/')}/api/embed",
        json={"model": settings.embedding_model, "input": [chunk.text for chunk in chunks]},
    )
    response.raise_for_status()
    return response.json()["embeddings"]


def _write_vectors(chunks: list[RawChunk], embeddings: list[list[float]]) -> None:
    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    embedding vector NOT NULL
                )
                """
            )
            cursor.executemany(
                """
                INSERT INTO document_chunks (chunk_id, content, source, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    source = EXCLUDED.source,
                    embedding = EXCLUDED.embedding
                """,
                [
                    (chunk.chunk_id, chunk.text, chunk.source, embedding)
                    for chunk, embedding in zip(chunks, embeddings, strict=True)
                ],
            )


def _write_lexical(chunks):
    backend = get_lexical_backend()
    if hasattr(backend, "index_documents"):
        backend.index_documents(chunks)


def embed_and_index(chunks: list[RawChunk]) -> None:  # pragma: no cover - integration
    if not chunks:
        return
    with httpx.Client(timeout=120.0) as client:
        embeddings = _embed(chunks, client)
    _write_vectors(chunks, embeddings)
    _write_lexical(chunks)
