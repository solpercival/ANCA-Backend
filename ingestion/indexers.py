"""Model-backed embedding plus PostgreSQL/pgvector and BM25 indexing."""
import json
from FlagEmbedding import BGEM3FlagModel
from pathlib import Path

# ingestion/indexers.py
from rag_engine.providers import get_lexical_backend

import httpx
import psycopg
from pgvector.psycopg import register_vector

from ingestion.chunker import RawChunk
from rag_engine.config import get_settings


def _dense_embed(chunks: list[RawChunk], client: httpx.Client) -> list[list[float]]:
    settings = get_settings()
    if settings != "dual":
        return [[]]
    
    response = client.post(
        f"{settings.ollama_base_url.rstrip('/')}/api/embed",
        json={"model": settings.embedding_model, "input": [chunk.text for chunk in chunks]},
    )
    response.raise_for_status()
    return response.json()["embeddings"]

def _sparse_embed(chunks: list[RawChunk], client: httpx.Client) -> list[dict[str,float]]:
    settings = get_settings()
    if settings != "dual":
        return [[]]
    
    response = client.post(f"", # add api endpoint for sparse model
                           json = {"input": [chunk.text for chunk in chunks]})
    response.raise_for_status()
    result = response.json() # array of array of dicts

    return [{entry["index"]: entry["value"] for entry in sparse_chunk} for sparse_chunk in result]

def _unified_embed(chunks: list[RawChunk], model: BGEM3FlagModel) -> dict[str,list]:
    settings = get_settings()
    if settings != "unified":
        return {}

    model: BGEM3FlagModel = BGEM3FlagModel('BAAI/bge-m3', use_fp16=False) # use_fp16=False when running on CPU
    output = model.encode([chunk.text for chunk in chunks], return_dense=True, return_sparse=True)

    return {"dense": output["dense_vecs"].tolist(), "sparse": output["lexical_weights"]}
    
def _write_embeddings(chunks: list[RawChunk], dense_embeddings: list[list[float]], sparse_embeddings: list[dict[str,float]]) -> None:
    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            # check if table created
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id BIGINT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    dc_type CHUNK_TYPE NOT NULL DEFAULT 'text',
                    document_chunkscol VARCHAR(45) NOT NULL,
                    lexical_embedding sparsevec(250002) NOT NULL,
                    semantic_embedding vector(1024) NOT NULL
                )
                """
            )

            insert_data = [(chunk.text, '{}', chunk.kind, "", sparse, dense) for 
                           chunk, sparse, dense in zip(chunks, sparse_embeddings, dense_embeddings)]

            cursor.execute(
                """
                INSERT INTO document_chunks (content, metadata, dc_type, document_chunkscol, lexical_embedding, semantic_embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
            )

def embed_and_index(chunks: list[RawChunk]) -> None:  # pragma: no cover - integration
    if not chunks:
        return

    settings = get_settings()
    if settings == "dual":
        with httpx.Client(timeout=120.0) as client:
            dense_embeddings = _dense_embed(chunks=chunks, client=client)
            sparse_embeddings = _sparse_embed(chunks=chunks, client=client)
    else:
        embeds = _unified_embed(chunks=chunks)
        dense_embeddings: list[list[float]] = embeds["dense"]
        sparse_embeddings: list[dict[str,float]] = embeds["sparse"]

    _write_embeddings(dense_embeddings=dense_embeddings, sparse_embeddings=sparse_embeddings)