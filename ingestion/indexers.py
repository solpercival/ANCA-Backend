"""Model-backed embedding plus PostgreSQL/pgvector."""
import json
from pathlib import Path
from collections import defaultdict

# ingestion/indexers.py
from rag_engine.providers import get_lexical_backend

import httpx
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from ingestion.chunker import RawChunk
from rag_engine.config import get_settings

def _dense_embed(chunks: list[RawChunk], client: httpx.Client) -> list[list[float]]:
    """
    Function for generating dense vector embeddings using ollama API. Returns a
    list of list of floats representing embeddings corresponding to input chunks.
    """
    settings = get_settings()
    batch_size = 32
    embeddings = []
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        response = client.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/embed",
            json={"model": settings.embedding_model, "input": [chunk.text for chunk in batch]},
        )
        response.raise_for_status()
        embeddings.extend(response.json()["embeddings"])
        print(f"dense embed: {min(start + batch_size, len(chunks))}/{len(chunks)}", flush=True)
    return embeddings

def _sparse_embed(chunks: list[RawChunk], client: httpx.Client) -> list[dict[str,float]]:
    """
    Function for generating sparse vector embeddings using tei container. Returns a
    list of dictionaries representing embeddings corresponding to input chunks.
    """
    settings = get_settings()
    if settings.embedding_setup != "dual":
        return []

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

def resolve_immediate_heading(cursor, chunk: RawChunk, doc_id: int,
                               heading_cache: dict[tuple, int]) -> int | None:
    """
    Walk the chunk's header cascade top-down (h1 -> h2 -> h3 ...), creating any
    heading rows that don't exist yet and chaining each one to its parent via
    parent_heading.

    Returns the id of the deepest/closest heading for this chunk
    (or None if the chunk has no headings above it), which is what gets
    stored directly on document_chunks.

    heading_cache is keyed by (doc_id, path) where path is the accumulated
    "h1:abc>h2:xyz" string, so repeated ancestor chains across chunks in the
    same document reuse the same heading row instead of duplicating it.
    """
    prefix = ""
    parent_id = None
    leaf_heading_id = None

    for level, text in chunk.header_cascade:
        prefix = f"{prefix}{level}:{text}"
        cache_key = (doc_id, prefix)

        if cache_key not in heading_cache:
            cursor.execute(
                """
                INSERT INTO heading (heading_order, hierarchy, document_id, parent_heading)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (document_id, parent_heading, heading_order) DO UPDATE
                    SET heading_order = EXCLUDED.heading_order
                RETURNING heading_id
                """,
                (text, level, doc_id, parent_id)
            )
            heading_cache[cache_key] = cursor.fetchone()["heading_id"]

        parent_id = heading_cache[cache_key]
        leaf_heading_id = parent_id
        prefix += ">"

    return leaf_heading_id


def insert_chunk(cursor, data: dict, doc_id: int, heading_cache: dict[tuple, int]) -> None:
    """Insert chunks into document_chunks table and insert headings if not exists"""

    chunk = data["chunk"]
    dense = data["dense"]
    sparse = data["sparse"] or None

    heading_id = resolve_immediate_heading(
        cursor=cursor, chunk=chunk, doc_id=doc_id, heading_cache=heading_cache
    )

    cursor.execute(
        """
        INSERT INTO document_chunks
            (content, metadata, dc_type, document_source, lexical_embedding, semantic_embedding, closest_heading)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING chunk_id
        """,
        (chunk.text, "{}", chunk.kind, chunk.source, f"{sparse}/30522" if sparse else None, dense, heading_id)
    )

def validate_tables(cursor) -> None:
    # FK dependencies means tables need to be created in a specific order
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document (
            doc_id SERIAL PRIMARY KEY,
            current_version VARCHAR(16) NOT NULL,
            hash BYTEA NOT NULL,
            file_path TEXT NOT NULL UNIQUE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS heading (
            heading_id BIGSERIAL PRIMARY KEY,
            heading_order TEXT NOT NULL,
            hierarchy VARCHAR(45) NOT NULL,
            document_id INTEGER NOT NULL,
            parent_heading BIGINT,
            CONSTRAINT prevent_duplicate_heading UNIQUE(document_id, parent_heading, heading_order),
            CONSTRAINT fk_heading_document
                FOREIGN KEY (document_id)
                REFERENCES document (doc_id)
                ON DELETE NO ACTION
                ON UPDATE NO ACTION,
            CONSTRAINT fk_heading_parent_heading
                FOREIGN KEY (parent_heading)
                REFERENCES heading (heading_id)
                ON DELETE NO ACTION
                ON UPDATE NO ACTION
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id BIGSERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            dc_type CHUNK_TYPE NOT NULL DEFAULT 'text',
            document_source TEXT NOT NULL,
            lexical_embedding sparsevec(30522),
            semantic_embedding vector(1024) NOT NULL,
            closest_heading BIGINT,
            CONSTRAINT fk_document_chunks_heading
                FOREIGN KEY (closest_heading)
                REFERENCES heading (heading_id)
                ON DELETE NO ACTION
		        ON UPDATE NO ACTION
        )
        """
    )
    cursor.execute(
        "ALTER TABLE document_chunks ALTER COLUMN lexical_embedding DROP NOT NULL"
    )
    cursor.execute(
        "ALTER TABLE heading ALTER COLUMN heading_order TYPE TEXT"
    )
    cursor.execute(
        "ALTER TABLE document ALTER COLUMN file_path TYPE TEXT"
    )
    cursor.execute(
        "ALTER TABLE document_chunks ALTER COLUMN document_source TYPE TEXT"
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
                doc_id = insert_document(cursor=cursor, version=1, hash=b"", file_path=doc)
                for chunk_group in doc_chunks[doc]:
                    insert_chunk(cursor=cursor, data=chunk_group, doc_id=doc_id, heading_cache=heading_cache)

            connection.commit()                                

def embed_and_index(chunks: list[RawChunk]) -> None:  # pragma: no cover - integration
    if not chunks:
        return

    settings = get_settings()
    with httpx.Client(timeout=600.0) as client:
        dense_embeddings = _dense_embed(chunks=chunks, client=client)
        sparse_embeddings = (
            _sparse_embed(chunks=chunks, client=client)
            if settings.embedding_setup == "dual"
            else [{} for _ in chunks]
        )
    
    _write_embeddings(chunks=chunks, dense_embeddings=dense_embeddings, sparse_embeddings=sparse_embeddings)

def populate_alarms(alarms_json: dict) -> None:
    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            for alarm in alarms_json["alarms"]:
                code_sections = alarm["code"].split(".")
                alarm_data = {
                    # alarm_code data
                    "origin": code_sections[0],
                    "sequence": code_sections[2],
                    "title": alarm["title"],
                    "severity_score": alarm["severity"], # added separate severity score (int)
                    "severity_category": alarm["severity_category"].lower(), # severity category (enum)
                    "alarm_text": alarm["alarm_text"],
                    "data_fields": alarm["data_fields"],

                    # alarm_module data
                    "code": code_sections[1],
                    "module_title": alarm["domain"]
                }

                # insert alarm module, ignore on conflict
                module_res = cursor.execute(
                    """
                    INSERT INTO alarm_module (code, title)
                    VALUES (%s, %s)
                    ON CONFLICT (code, title) DO UPDATE 
                    SET title = EXCLUDED.title
                    RETURNING id
                    """,
                    (alarm_data["code"], alarm_data["module_title"]),
                ).fetchone()

                # insert alarm code, update details on conflict
                cursor.execute(
                    """
                    INSERT INTO alarm_code
                    (origin, alarm_sequence, title, severity_score, severity_category, alarm_text, data_fields, module)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (origin, alarm_sequence, module) DO UPDATE 
                        SET title = EXCLUDED.title,
                            severity_score = EXCLUDED.severity_score,
                            severity_category = EXCLUDED.severity_category,
                            alarm_text = EXCLUDED.alarm_text,
                            data_fields = EXCLUDED.data_fields; 
                    """,
                    (alarm_data["origin"], alarm_data["sequence"], alarm_data["title"],
                     alarm_data["severity_score"], alarm_data["severity_category"], 
                     alarm_data["alarm_text"], Jsonb(alarm_data["data_fields"]), module_res["id"]),
                )

            connection.commit()
