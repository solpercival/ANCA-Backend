from dataclasses import dataclass
import psycopg
from rag_engine.retrieval.interfaces import Chunk, Embedder, LexicalIndex, VectorStore
from db import get_conn
from rag_engine.config import get_settings

class PostgresDBConnection:
    # VectorStore search
    async def semantic_search(self, vector: list[float], top_k: int, where: dict[str, str] | None = None) -> list[Chunk]:
        result_chunks = []

        if not vector or top_k < 1:
            return []
        
        with get_conn() as cursor:
            cursor.execute(
                """
                SELECT dc.chunk_id, dc.content, dc.metadata, doc.file_path, dc.distance
                FROM (
                    SELECT chunk_id, content, metadata, semantic_embedding <=> %s AS distance
                    FROM document_chunks
                    ORDER BY distance
                    LIMIT %s
                ) dc
                JOIN chunk_headings ch ON ch.doc_chunks_id = dc.chunk_id
                JOIN heading head ON head.heading_id = ch.heading_id
                JOIN document doc ON doc.doc_id = head.document_id
                ORDER BY dc.distance;
                """, 
                (vector, top_k),
            )

            result = cursor.fetchall()
            for entry in result:
                result_chunks.append(Chunk(chunk_id=entry["chunk_id"], text=entry["content"], source=entry["file_path"], metadata=entry["metadata"]))

        return result_chunks

    async def lexical_search(self, vector: dict[int,float], top_k: int) -> list[Chunk]:
        result_chunks = []
        settings = get_settings()

        if not vector or top_k < 1:
            return []
        
        with get_conn() as cursor:
            cursor.execute(
                """
                SELECT dc.chunk_id, dc.content, dc.metadata, doc.file_path, dc.distance
                FROM (
                    SELECT chunk_id, content, metadata, lexical_embedding <#> %s AS distance
                    FROM document_chunks
                    ORDER BY distance
                    LIMIT %s
                ) dc
                JOIN chunk_headings ch ON ch.doc_chunks_id = dc.chunk_id
                JOIN heading head ON head.heading_id = ch.heading_id
                JOIN document doc ON doc.doc_id = head.document_id
                ORDER BY dc.distance;
                """, 
                (f"{vector}/{settings.lexical_dim}", top_k),
            )

            result = cursor.fetchall()
            for entry in result:
                result_chunks.append(Chunk(chunk_id=entry["chunk_id"], text=entry["content"], source=entry["file_path"], metadata=entry["metadata"]))

            return result_chunks