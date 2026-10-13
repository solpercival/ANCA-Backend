"""Postgres and Redis adapters behind the retrieval interfaces.

PostgresDBConnection implements VectorStore (semantic/lexical search), the keyword
lookup and the chat store (conversation context read/write) from
rag_engine.retrieval.interfaces; RedisConnection implements ResponseCache. The
connection pool is synchronous psycopg, so every async method runs its query in a
worker thread through a `_*_sync` helper (see the PostgresDBConnection docstring).
"""

import asyncio
import datetime
import hashlib
import json
import re

from pgvector import Vector

from rag_engine.auth.tiers import DocAudience
from rag_engine.config import get_settings
from rag_engine.retrieval.interfaces import Chunk, Where
from rag_engine.stores.cache import get_cache_conn
from rag_engine.stores.db import get_db_conn


def _doc_audience_condition(where: Where | None) -> tuple[str, list[str]] | None:
    """SQL predicate and its parameter for where["doc_audiences"], or None when the
    key is absent (all documents). The chunk's document_source must contain one of
    the audiences' folders; an empty list matches nothing. Shared by the semantic
    and lexical searches so the tier rule is applied identically by both."""
    if not where or "doc_audiences" not in where:
        return None
    patterns = [f"%{DocAudience(a).path_fragment}%" for a in where["doc_audiences"]]
    return "document_source LIKE ANY(%s)", patterns


# Select-list column giving a chunk's heading text as `section` (NULL when it has no
# closest_heading). heading.heading_order holds the heading's text. Equivalent to a
# LEFT JOIN on heading's primary key, written as a scalar subquery so the searches'
# FROM / ORDER BY distance / LIMIT shape -- and so the vector index scan -- is
# unchanged and only the returned rows look their heading up. Shared by both searches.
_SECTION_COLUMN = """(
                        SELECT h.heading_order FROM heading h
                        WHERE h.heading_id = document_chunks.closest_heading
                    ) AS section"""


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
        self, vector: list[float], top_k: int, where: Where | None = None
    ) -> list[Chunk]:
        """Nearest chunks by cosine distance on the dense embedding."""
        if not vector or top_k < 1:
            return []
        return await asyncio.to_thread(self._semantic_search_sync, vector, top_k, where)

    def _semantic_search_sync(
        self, vector: list[float], top_k: int, where: Where | None
    ) -> list[Chunk]:
        """Blocking query for semantic_search; runs in a worker thread."""
        result_chunks = []

        with get_db_conn() as conn:
            query_str = f"""
                SELECT chunk_id, content, metadata, document_source AS file_path,
                    semantic_embedding <=> %s AS distance,
                    {_SECTION_COLUMN}
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
                audience = _doc_audience_condition(where)
                if audience:
                    where_conditions.append(audience[0])
                    params.append(audience[1])

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
                        section=entry["section"] or None,
                    )
                )

        return result_chunks

    # Lexical index search
    async def lexical_search(
        self, vector: dict[int, float], top_k: int, where: Where | None = None
    ) -> list[Chunk]:
        """Best chunks by inner product on the sparse (lexical) embedding."""
        if not vector or top_k < 1:
            return []
        return await asyncio.to_thread(self._lexical_search_sync, vector, top_k, where)

    def _lexical_search_sync(
        self, vector: dict[int, float], top_k: int, where: Where | None
    ) -> list[Chunk]:
        """Blocking query for lexical_search; runs in a worker thread."""
        result_chunks = []
        settings = get_settings()

        with get_db_conn() as conn:
            query_str = f"""
                SELECT chunk_id, content, metadata, document_source AS file_path,
                    lexical_embedding <#> %s AS distance,
                    {_SECTION_COLUMN}
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
                audience = _doc_audience_condition(where)
                if audience:
                    query_str += f"AND {audience[0]}\n"
                    params.append(audience[1])

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
                        section=entry["section"] or None,
                    )
                )

            return result_chunks

    # SectionStore lookup
    async def section_texts(self, chunk_ids: list[str]) -> dict[str, tuple[str, str]]:
        """Each chunk's whole section: the text of every chunk under the same
        heading, joined in document order, keyed by chunk id as (heading id, text).
        Ingestion cuts a section into text, list, table and code pieces; this puts
        them back together. Chunks without a heading are left out."""
        ids = [int(i) for i in chunk_ids if str(i).isdigit()]
        if not ids:
            return {}
        return await asyncio.to_thread(self._section_texts_sync, ids)

    def _section_texts_sync(self, ids: list[int]) -> dict[str, tuple[str, str]]:
        """Blocking query for section_texts; runs in a worker thread."""
        with get_db_conn() as conn:
            # chunk_id is assigned in insertion order, which is document order within
            # a file; a heading row belongs to one document, so matching on it alone
            # stays inside the selected chunk's file
            result = conn.execute(
                """
                SELECT sel.chunk_id AS selected, sel.closest_heading AS heading_id,
                    string_agg(c.content, E'\\n\\n' ORDER BY c.chunk_id) AS section_text
                FROM document_chunks sel
                JOIN document_chunks c ON c.closest_heading = sel.closest_heading
                WHERE sel.chunk_id = ANY(%s)
                GROUP BY sel.chunk_id, sel.closest_heading;
                """,
                [ids],
            ).fetchall()
        return {
            str(entry["selected"]): (str(entry["heading_id"]), entry["section_text"])
            for entry in result
        }

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
        """Save one query/response turn, linked to its alarm when alarm_str names one
        in the catalogue ("<origin>.<module>.<sequence>"); otherwise saved unlinked."""
        settings = get_settings()

        with get_db_conn() as conn:
            alarm_id = None
            parts = alarm_str.split(settings.alarm_delim) if alarm_str else []
            if len(parts) == 3:
                result = conn.execute(
                    """
                    SELECT ac.alarm_code_id AS alarm_id FROM alarm_code ac
                    JOIN alarm_module am ON am.id = ac.module
                    WHERE ac.origin = %s AND am.code = %s AND ac.alarm_sequence = %s;
                """,
                    parts,
                ).fetchone()
                if result:
                    alarm_id = result["alarm_id"]

            # user id and feedback currently not collected, option to add later
            conn.execute(
                """
                INSERT INTO response
                (conversation_id, query, response_body, time_generated, alarm_id)
                VALUES (%s, %s, %s, %s, %s);
            """,
                [conversation_id, query, response, datetime.datetime.now(), alarm_id],
            )

            conn.commit()


class RedisConnection:
    """Generated-answer cache in Redis (ResponseCache). Off unless
    RESPONSE_CACHE_ENABLED is set; see Orchestrator._generation_cache_key for what
    an entry is keyed on.

    The client from get_cache_conn is synchronous, so each async method runs its
    command in a worker thread through a `_*_sync` helper, like PostgresDBConnection.
    """

    def _create_key(self, text: str) -> str:
        """Redis key for `text`: RESPONSE_PREFIX and its SHA-256 hex digest, so keys
        have a fixed length whatever the text contains."""
        digest = hashlib.sha256(text.encode()).hexdigest()
        return f"{get_settings().response_prefix}{digest}"

    async def add_response(self, query: str, response: str) -> None:
        """Cache `response` under `query` for RESPONSE_TTL seconds. No-op without Redis."""
        await asyncio.to_thread(self._add_response_sync, query, response)

    def _add_response_sync(self, query: str, response: str) -> None:
        """Blocking write for add_response; runs in a worker thread."""
        with get_cache_conn() as client:
            if not client:
                return
            client.set(self._create_key(query), response, ex=get_settings().response_ttl)

    async def retrieve_response(self, query: str) -> str | None:
        """The response cached under this exact `query`, or None on a miss or
        without Redis."""
        return await asyncio.to_thread(self._retrieve_response_sync, query)

    def _retrieve_response_sync(self, query: str) -> str | None:
        """Blocking read for retrieve_response; runs in a worker thread."""
        with get_cache_conn() as client:
            if not client:
                return None
            return client.get(self._create_key(query)) or None
