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
            query_str = """
                SELECT chunk_id, content, metadata, document_source AS file_path,
                    semantic_embedding <=> %s AS distance
                FROM document_chunks
            """
            params = [Vector(vector)]

            if where:
                where_conditions = []
                if "machine_variant" in where:
                    where_conditions.append("metadata->>'machine_variant' = %s")
                    params.append(where["machine_variant"])
                if "versions" in where:
                    versions_json = json.dumps(where["versions"])
                    where_conditions.append("metadata->'versions' @> %s::jsonb")
                    params.append(versions_json)

                if where_conditions:
                    query_str += "WHERE " + " AND ".join(where_conditions) + "\n"

            query_str += """ORDER BY distance
                LIMIT %s;
            """
            params.append(top_k)

            result = conn.execute(query_str, params).fetchall()
            for entry in result:
                result_chunks.append(Chunk(chunk_id=str(entry["chunk_id"]), text=entry["content"], source=entry["file_path"], metadata=entry["metadata"]))

        return result_chunks

    # Lexical index search
    async def lexical_search(self, vector: dict[int,float], top_k: int, where: dict[str, str] | None = None) -> list[Chunk]:
        result_chunks = []
        settings = get_settings()

        if not vector or top_k < 1:
            return []

        with get_db_conn() as conn:
            query_str = f"""
                SELECT chunk_id, content, metadata, document_source AS file_path,
                    lexical_embedding <#> %s AS distance
                FROM document_chunks
                WHERE lexical_embedding IS NOT NULL
            """
            params = [f"{vector}/{settings.lexical_dim}"]

            if where:
                if "machine_variant" in where:
                    query_str += "AND metadata->>'machine_variant' = %s\n"
                    params.append(where["machine_variant"])
                if "versions" in where:
                    versions_json = json.dumps(where["versions"])
                    query_str += "AND metadata->'versions' @> %s::jsonb\n"
                    params.append(versions_json)

            query_str += """ORDER BY distance
                LIMIT %s;
            """
            params.append(top_k)

            result = conn.execute(query_str, params).fetchall()
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