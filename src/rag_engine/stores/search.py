from rag_engine.retrieval.interfaces import Chunk, Alarm
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

    # Lexical index search
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

    async def alarm_search(self, request_json: dict) -> Alarm:
        settings = get_settings()

        # validate fields
        if (not request_json) or ("code" not in request_json) or ("env" not in request_json):
            return None

        alarm_code = request_json["code"].split(".")

        # validate alarm code format
        if len(alarm_code) != 3:
            return None

        with get_db_conn() as conn:
            result = conn.execute(
                """
                SELECT 
                    am.code as module, am.title as domain,
                    ac.origin as origin, 
                    ac.sequence as sequence,
                    ac.title as title,
                    ac.severity_category as severity_category, 
                    ac.severity_score as severity_score,
                    ac.alarm_text as alarm_text,
                    ac.data_fields as data_fields
                FROM alarm_code ac
                INNER JOIN alarm_module am
                ON ac.id = am.module
                WHERE ac.origin = %s AND am.code = %s AND ac.sequence = %s;
                """,
                (alarm_code[0], alarm_code[1], alarm_code[2])
            ).fetchone()

            # no results
            if not result:
                return None

        return Alarm(code=request_json["code"], title=result["title"], domain=result["domain"],
                    severity_score=result["severity_score"], alarm_text=result["alarm_text"], 
                    data_fields=json.loads(result["data_fields"]))

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