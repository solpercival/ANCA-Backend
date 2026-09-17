from rag_engine.retrieval.interfaces import Chunk
from rag_engine.stores.db import get_db_conn
from rag_engine.stores.cache import get_cache_conn
from rag_engine.config import get_settings
from pgvector import Vector
import json
import hashlib

class PostgresDBConnection:
    # VectorStore search
    async def semantic_search(self, vector: list[float], top_k: int, where: dict[str, str] | None = None) -> list[Chunk]:
        result_chunks = []

        if not vector or top_k < 1:
            return []
        
        with get_db_conn() as conn:
            result = conn.execute(
                """
                SELECT chunk_id, content, metadata, document_source AS file_path,
                    semantic_embedding <=> %s AS distance
                FROM document_chunks
                ORDER BY distance
                LIMIT %s;
                """, 
                (Vector(vector), top_k),
            ).fetchall()
            for entry in result:
                result_chunks.append(Chunk(chunk_id=str(entry["chunk_id"]), text=entry["content"], source=entry["file_path"], metadata=entry["metadata"]))

        return result_chunks

    async def lexical_search(self, vector: dict[int,float], top_k: int) -> list[Chunk]:
        result_chunks = []
        settings = get_settings()

        if not vector or top_k < 1:
            return []
        
        with get_db_conn() as conn:
            result = conn.execute(
                """
                SELECT chunk_id, content, metadata, document_source AS file_path,
                    lexical_embedding <#> %s AS distance
                FROM document_chunks
                WHERE lexical_embedding IS NOT NULL
                ORDER BY distance
                LIMIT %s;
                """, 
                (f"{vector}/{settings.lexical_dim}", top_k),
            ).fetchall()
            for entry in result:
                result_chunks.append(Chunk(chunk_id=str(entry["chunk_id"]), text=entry["content"], source=entry["file_path"], metadata=entry["metadata"]))

            return result_chunks

class RedisConnection:
    def _create_key(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()
    
    async def add_chunk(self, chunk: Chunk) -> None:
        with get_cache_conn() as client:
            if not client:
                return
            settings = get_settings()
            client.set(self._create_key(f"{settings.chunks_prefix}{chunk.chunk_id}"), str(chunk), ex=settings.chunks_ttl)

    async def retrieve_chunk(self, chunk_id: str) -> Chunk | None:
        with get_cache_conn() as client:
            if not client:
                return None

            settings = get_settings()
            result = client.get(self._create_key(f"{settings.chunks_prefix}{chunk_id}"))
            if not result:
                return 
            
            json_result = json.loads(result)
            return Chunk(chunk_id=json_result["chunk_id"], 
                         text=json_result["text"], 
                         source=json_result["source"],
                         metadata=json_result["metadata"],
                         score=json_result["score"])

    async def add_response(self, query: str, response: str) -> None:
        with get_cache_conn() as client:
            if not client:
                return
            settings = get_settings()
            client.set(self._create_key(f"{settings.response_prefix}{query}"), json.dumps({"response": response}, default=str), ex=settings.response_ttl)

    async def retrieve_response(self, query: str) -> str | None:
        with get_cache_conn() as client:
            if not client:
                return None

            settings = get_settings()
            result = client.get(self._create_key(f"{settings.response_prefix}{query}"))
            if not result:
                return 
            
            return json.loads(result)