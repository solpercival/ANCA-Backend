"""Model-backed embedding plus PostgreSQL/pgvector and BM25 indexing."""
import json
from pathlib import Path
from collections import defaultdict

# ingestion/indexers.py
from rag_engine.providers import get_lexical_backend

import httpx
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from ingestion.chunker import RawChunk
from rag_engine.config import get_settings

def _dense_embed(chunks: list[RawChunk], client: httpx.Client) -> list[list[float]]:
    """
    Function for generating dense vector embeddings using ollama API. Returns a
    list of list of floats representing embeddings corresponding to input chunks.
    """
    settings = get_settings()
    if settings.embedding_setup != "dual":
        return [[]]
    
    response = client.post(
        f"{settings.ollama_base_url.rstrip('/')}/api/embed",
        json={"model": settings.embedding_model, "input": [chunk.text for chunk in chunks]},
    )
    response.raise_for_status()
    return response.json()["embeddings"]

def _sparse_embed(chunks: list[RawChunk], client: httpx.Client) -> list[dict[str,float]]:
    """
    Function for generating sparse vector embeddings using tei container. Returns a
    list of dictionaries representing embeddings corresponding to input chunks.
    """
    settings = get_settings()
    if settings.embedding_setup != "dual":
        return [[]]

    sparse_vecs = client.post(
        f"{settings.tei_endpoint.rstrip('/')}/embed_sparse",
        json={"inputs": [chunk.text for chunk in chunks]},
    ).raise_for_status().json()
    
    return [{int(entry["index"]): float(entry["value"]) for entry in sparse_chunk} for sparse_chunk in sparse_vecs]

def insert_document(cursor, version: str, hash: str, file_path: str) -> int:
    """Inserts single document into documents table"""
    res = cursor.execute(
        """
        INSERT INTO document (current_version, hash, file_path)
        VALUES (%s, %s, %s)
        ON CONFLICT (file_path)
        DO UPDATE SET current_version = EXCLUDED.current_version, hash = EXCLUDED.hash
        RETURNING doc_id
        """,
        (version, hash, file_path)
    ).fetchone()

    return res["doc_id"]

def insert_chunk(cursor, data: dict, doc_id: int, heading_cache: dict[tuple, int]) -> None:
    """Insert chunks into document_chunks table and insert headings if not exists"""
    heading_ids = []
    chunk = data["chunk"]
    dense = data["dense"]
    print(f"DENSE: {len(dense)}")
    sparse = data["sparse"]

    for header in chunk.headers:
        header_key = (str(header), "h1", doc_id)

        if header_key not in heading_cache:
            cursor.execute(
                """
                INSERT INTO heading (heading_order, hierarchy, document_id)
                VALUES (%s, %s, %s)
                RETURNING heading_id
                """,
                header_key
            )
            heading_id = cursor.fetchone()["heading_id"]
            heading_cache[header_key] = heading_id

        heading_ids.append(heading_cache[header_key])

    cursor.execute(
        """
        INSERT INTO document_chunks
            (content, metadata, dc_type, document_chunkscol, lexical_embedding, semantic_embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING chunk_id
        """,
        (chunk.text, "{}", chunk.kind, chunk.source, f"{sparse}/30522", dense)
    )
    chunk_id = cursor.fetchone()["chunk_id"]

    if heading_ids and chunk_id:
        cursor.executemany(
            """
            INSERT INTO chunk_headings (heading_id, doc_chunks_id)
            VALUES (%s, %s)
            """,
            [(h_id, chunk_id) for h_id in heading_ids]
        )

def validate_tables(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            dc_type CHUNK_TYPE NOT NULL DEFAULT 'text',
            document_chunkscol VARCHAR(45) NOT NULL,
            lexical_embedding sparsevec(30522) NOT NULL,
            semantic_embedding vector(768) NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document (
            doc_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            current_version VARCHAR(16) NOT NULL,
            hash CHAR(64) NOT NULL,
            file_path VARCHAR(120) NOT NULL UNIQUE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS heading (
            heading_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            heading_order VARCHAR(45) NOT NULL,
            hierarchy VARCHAR(45) NOT NULL,
            document_id INTEGER REFERENCES document(doc_id) NOT NULL,
            CONSTRAINT prevent_duplicate_heading UNIQUE(heading_order, document_id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_headings (
            heading_id BIGINT REFERENCES heading(heading_id) NOT NULL,
            doc_chunks_id BIGINT REFERENCES document_chunks(chunk_id) NOT NULL,
            PRIMARY KEY (heading_id, doc_chunks_id)
        )
        """
    )
    
def _write_embeddings(chunks: list[RawChunk], dense_embeddings: list[list[float]], sparse_embeddings: list[dict[str,float]]) -> None:
    doc_chunks: dict[str, list[dict[str,list|RawChunk]]] = defaultdict(list)

    # Group chunks, dense and sparse embeddings together using source document as key
    for i in range(len(chunks)):
        doc_chunks[chunks[i].source].append({"chunk": chunks[i], "dense": dense_embeddings[i], "sparse": sparse_embeddings[i]})

    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            # check if tables created
            validate_tables(cursor=cursor)
            heading_cache = {}

            # insert document into table
            for doc in doc_chunks:
                doc_id = insert_document(cursor=cursor, version=1, hash="", file_path=doc)
                for chunk_group in doc_chunks[doc]:
                    insert_chunk(cursor=cursor, data=chunk_group, doc_id=doc_id, heading_cache=heading_cache)

            connection.commit()                                

def embed_and_index(chunks: list[RawChunk]) -> None:  # pragma: no cover - integration
    if not chunks:
        return

    settings = get_settings()
    with httpx.Client(timeout=120.0) as client:
        dense_embeddings = _dense_embed(chunks=chunks, client=client)
        sparse_embeddings = _sparse_embed(chunks=chunks, client=client)
    
    _write_embeddings(chunks=chunks, dense_embeddings=dense_embeddings, sparse_embeddings=sparse_embeddings)