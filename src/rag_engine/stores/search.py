"""Postgres and Redis adapters behind the retrieval interfaces.

PostgresDBConnection implements VectorStore (semantic/lexical search), the keyword
lookup and the chat store (conversation context read/write) from
rag_engine.retrieval.interfaces. The connection pool is synchronous psycopg, so
every async method runs its query in a worker thread through a `_*_sync` helper
(see the PostgresDBConnection docstring).
"""

import asyncio
import datetime
import hashlib
import json
import re

from pgvector import Vector

from rag_engine.config import get_settings
from rag_engine.retrieval.interfaces import Alarm, Chunk
from rag_engine.stores.cache import get_cache_conn
from rag_engine.stores.db import get_db_conn


class PostgresDBConnection:
    """Postgres-backed retrieval stores.

    Threading rule: the pool from get_db_conn is synchronous psycopg, so an async
    method must never query it directly -- that blocks the event loop and every
    concurrent request waits on the DB. Each async method validates its input,
    then runs a `_<name>_sync` helper with asyncio.to_thread. When adding a query,
    follow the same split. store_query_result is sync by interface and is called
    from sync code.
    """

    # VectorStore search
    async def semantic_search(
        self, vector: list[float], top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]:
        """Nearest chunks by cosine distance on the dense embedding."""
        if not vector or top_k < 1:
            return []
        return await asyncio.to_thread(self._semantic_search_sync, vector, top_k, where)

    def _semantic_search_sync(
        self, vector: list[float], top_k: int, where: dict[str, str] | None
    ) -> list[Chunk]:
        """Blocking query for semantic_search; runs in a worker thread."""
        result_chunks = []

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
                result_chunks.append(
                    Chunk(
                        chunk_id=str(entry["chunk_id"]),
                        text=entry["content"],
                        source=entry["file_path"],
                        metadata=entry["metadata"],
                    )
                )

        return result_chunks

    # Lexical index search
    async def lexical_search(
        self, vector: dict[int, float], top_k: int, where: dict[str, str] | None = None
    ) -> list[Chunk]:
        """Best chunks by inner product on the sparse (lexical) embedding."""
        if not vector or top_k < 1:
            return []
        return await asyncio.to_thread(self._lexical_search_sync, vector, top_k, where)

    def _lexical_search_sync(
        self, vector: dict[int, float], top_k: int, where: dict[str, str] | None
    ) -> list[Chunk]:
        """Blocking query for lexical_search; runs in a worker thread."""
        result_chunks = []
        settings = get_settings()

        with get_db_conn() as conn:
            query_str = """
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
                result_chunks.append(
                    Chunk(
                        chunk_id=str(entry["chunk_id"]),
                        text=entry["content"],
                        source=entry["file_path"],
                        metadata=entry["metadata"],
                    )
                )

            return result_chunks

    # AlarmStore search. Not used on the request path (PostgresAlarmStore in
    # stores/alarms.py is), and its SQL names columns the schema doesn't have
    # (ac.sequence, ac.id); left as-is pending a decision on removing it.
    async def alarm_search(self, request_json: dict) -> Alarm:
        """Unused legacy lookup: the alarm for request_json["code"], or None if the
        request lacks `code`/`env` or the code isn't three dot-separated parts.
        Use PostgresAlarmStore.get_alarm instead."""
        # validate fields
        if (not request_json) or ("code" not in request_json) or ("env" not in request_json):
            return None

        alarm_code = request_json["code"].split(".")

        # validate alarm code format
        if len(alarm_code) != 3:
            return None

        return await asyncio.to_thread(self._alarm_search_sync, request_json["code"], alarm_code)

    def _alarm_search_sync(self, code: str, alarm_code: list[str]) -> Alarm | None:
        """Blocking query for alarm_search; runs in a worker thread."""
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
                (alarm_code[0], alarm_code[1], alarm_code[2]),
            ).fetchone()

            # no results
            if not result:
                return None

        return Alarm(
            code=code,
            title=result["title"],
            domain=result["domain"],
            severity_score=result["severity_score"],
            alarm_text=result["alarm_text"],
            data_fields=json.loads(result["data_fields"]),
        )

    # KeywordStore search
    async def keyword_search(self, query: str, top_k: int) -> list[str]:
        """Domain keywords matching the query: exact/alias matches first, then fuzzy
        (trigram) matches, ranked by score then IDF. None when nothing matches."""
        # validate fields
        if (not query) or (top_k < 1):
            return None

        query_parts = re.split(r"[ ,!. ]+", query.strip())
        query_parts = [word for word in query_parts if word]  # filter out empty strings

        return await asyncio.to_thread(self._keyword_search_sync, query_parts, top_k)

    def _keyword_search_sync(self, query_parts: list[str], top_k: int) -> list[str] | None:
        """Blocking query for keyword_search; runs in a worker thread."""
        with get_db_conn() as conn:
            result = conn.execute(
                """
                WITH exact_match AS (
                    SELECT keyword, idf_weight, 1.0::real AS score, 'exact' AS match_type
                    FROM keyword_lookup
                    WHERE keyword = %(q)s
                    OR aliases @> ARRAY[%(q)s]::text[]
                ),
                fuzzy_match AS (
                    SELECT keyword, idf_weight,
                        similarity(keyword, %(q)s) AS score,
                        'fuzzy' AS match_type
                    FROM keyword_lookup
                    WHERE keyword %% %(q)s
                    AND NOT EXISTS (
                        SELECT 1 FROM exact_match e WHERE e.keyword = keyword_lookup.keyword
                    )
                )
                SELECT keyword, score, match_type
                FROM (
                    SELECT * FROM exact_match
                    UNION ALL
                    SELECT * FROM fuzzy_match
                ) combined
                ORDER BY score DESC, idf_weight DESC
                LIMIT %(limit)s
            """,
                {"q": query_parts, "limit": top_k},
            ).fetchall()

            if not result:
                return None

            return [entry["keyword"] for entry in result]

    async def context_search(self, conversation_id: str) -> list[tuple[str, bool | None]]:
        """The conversation's past turns, oldest first, as alternating
        (query, None) and (response, user_feedback) pairs."""
        if not conversation_id:
            return None

        return await asyncio.to_thread(self._context_search_sync, conversation_id)

    def _context_search_sync(self, conversation_id: str) -> list[tuple[str, bool | None]]:
        """Blocking query for context_search; runs in a worker thread."""
        context_result: list[tuple[str, bool | None]] = []
        with get_db_conn() as conn:
            result = conn.execute(
                """
                SELECT query, response_body, user_feedback FROM response
                WHERE conversation_id = %s
                ORDER BY time_generated ASC;
            """,
                [conversation_id],
            ).fetchall()

            for entry in result:
                context_result.append((entry["query"], None))
                context_result.append((entry["response_body"], entry["user_feedback"]))

        return context_result

    def store_query_result(
        self, conversation_id: str, query: str, response: str, alarm_str: str | None
    ) -> None:
        """Save one query/response turn, linked to its alarm when alarm_str is given.

        Known issue: the alarm lookup filters alarm_code on `code` and `sequence`,
        which the schema doesn't have (it has `module` and `alarm_sequence`), so a
        call with alarm_str raises and /resolve logs store_context_failed.
        """
        settings = get_settings()

        with get_db_conn() as conn:
            if alarm_str:
                # add alarm if exists
                result = conn.execute(
                    """
                    SELECT alarm_code_id AS alarm_id FROM alarm_code
                    WHERE origin = %s AND code = %s AND sequence = %s;                
                """,
                    alarm_str.split(settings.alarm_delim),
                ).fetchone()

                if not result:
                    return None
                alarm_id = result["alarm_id"]

                conn.execute(
                    """
                    INSERT INTO response
                    (conversation_id, query, response_body, time_generated, alarm_id) 
                    VALUES (%s, %s, %s, %s, %s);
                """,
                    [conversation_id, query, response, datetime.datetime.now(), alarm_id],
                )  # user id and feedback currently not collected, option to add later
            else:
                # insert without alarm_id and user_id
                conn.execute(
                    """
                    INSERT INTO response
                    (conversation_id, query, response_body, time_generated) 
                    VALUES (%s, %s, %s, %s);
                """,
                    [conversation_id, query, response, datetime.datetime.now()],
                )

            conn.commit()


class RedisConnection:
    """Chunk/response cache in Redis. Nothing in src/ uses it yet.

    The client from get_cache_conn is synchronous, so these async methods block the
    event loop; before putting them on a request path, give them the same
    asyncio.to_thread split as PostgresDBConnection.
    """

    def _create_key(self, text: str) -> str:
        """Redis key for `text`: its SHA-256 hex digest, so keys have a fixed length
        whatever the query or chunk id contains."""
        return hashlib.sha256(text.encode()).hexdigest()

    async def add_chunk(self, chunk: Chunk) -> None:
        """Cache a chunk under its id for CHUNKS_TTL seconds. No-op without Redis."""
        with get_cache_conn() as client:
            if not client:
                return
            settings = get_settings()
            client.set(
                self._create_key(f"{settings.chunks_prefix}{chunk.chunk_id}"),
                str(chunk),
                ex=settings.chunks_ttl,
            )

    async def retrieve_chunk(self, chunk_id: str) -> Chunk | None:
        """The cached chunk, or None if it was never cached, expired, or Redis is down."""
        with get_cache_conn() as client:
            if not client:
                return None

            settings = get_settings()
            result = client.get(self._create_key(f"{settings.chunks_prefix}{chunk_id}"))
            if not result:
                return

            json_result = json.loads(result)
            return Chunk(
                chunk_id=json_result["chunk_id"],
                text=json_result["text"],
                source=json_result["source"],
                metadata=json_result["metadata"],
                score=json_result["score"],
            )

    async def add_response(self, query: str, response: str) -> None:
        """Cache the response to an exact query string for RESPONSE_TTL seconds.
        No-op without Redis."""
        with get_cache_conn() as client:
            if not client:
                return
            settings = get_settings()
            client.set(
                self._create_key(f"{settings.response_prefix}{query}"),
                json.dumps({"response": response}, default=str),
                ex=settings.response_ttl,
            )

    async def retrieve_response(self, query: str) -> str | None:
        """The cached entry for this exact query, or None on a miss. Note it returns
        the stored object, {"response": ...}, not the bare response string."""
        with get_cache_conn() as client:
            if not client:
                return None

            settings = get_settings()
            result = client.get(self._create_key(f"{settings.response_prefix}{query}"))
            if not result:
                return

            return json.loads(result)
