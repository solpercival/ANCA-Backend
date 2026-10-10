"""Model-backed embedding plus PostgreSQL/pgvector: the write side of retrieval.

- embed_and_index: embed chunks (Ollama dense, TEI sparse when EMBEDDING_SETUP=dual)
  and write document / heading / document_chunks rows, replacing each document's
  previous rows in one transaction. document.hash stores the file's SHA-256 hex
  digest when the caller supplies one.
  prune deletes documents missing from keep_paths; files skipped
  because their hash matched stay in that list so their chunks are kept.
- populate_alarms: upsert the alarm catalogue (alarm_module, alarm_code).
- populate_keyword_table: rebuild keyword_lookup, the domain-term index used by
  query rewriting.

Each function opens its own connection (not the app's pool): this module runs in
the offline ingestion job. Tables must already exist (Alembic migrations).
"""

import math

# ingestion/indexers.py
import re
from collections import defaultdict

import httpx
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from wordfreq import word_frequency

from ingestion.chunker import RawChunk
from rag_engine.config import get_settings


class InvalidInputError(Exception):
    """An alarms file entry is malformed; names the offending fields."""

    def __init__(self, invalid_fields: list):
        self.message = (
            "Input has invalid fields or in an invalid format. "
            f"Invalid fields: {', '.join(invalid_fields)}."
        )
        super().__init__(self.message)


# must match the SEVERITY enum in migration 0001
VALID_SEVERITY: tuple[str] = ("debug", "info", "warning", "error", "fatal")


def _dense_embed(chunks: list[RawChunk], client: httpx.Client) -> list[list[float]]:
    """
    Function for generating dense vector embeddings using ollama API. Returns a
    list of list of floats representing embeddings corresponding to input chunks.
    """
    settings = get_settings()
    batch_size = 32
    embeddings = []
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        response = client.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/embed",
            json={"model": settings.embedding_model, "input": [chunk.text for chunk in batch]},
        )
        response.raise_for_status()
        embeddings.extend(response.json()["embeddings"])
        print(f"dense embed: {min(start + batch_size, len(chunks))}/{len(chunks)}", flush=True)
    return embeddings


def _sparse_embed(chunks: list[RawChunk], client: httpx.Client) -> list[dict[str, float]]:
    """
    Function for generating sparse vector embeddings using tei container. Returns a
    list of dictionaries representing embeddings corresponding to input chunks.
    """
    settings = get_settings()
    if settings.embedding_setup != "dual":
        return []

    sparse_vecs = (
        client.post(
            f"{settings.tei_endpoint.rstrip('/')}/embed_sparse",
            json={"inputs": [chunk.text for chunk in chunks]},
        )
        .raise_for_status()
        .json()
    )

    return [
        {int(entry["index"]): float(entry["value"]) for entry in sparse_chunk}
        for sparse_chunk in sparse_vecs
    ]


def _document_hash_text(value: object) -> str:
    """Decode document.hash to the hex digest string, or "" when it is empty."""
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, bytearray):
        value = bytes(value)
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    if value is None:
        return ""
    return str(value)


def load_document_hashes() -> dict[str, str]:
    """file_path -> document.hash, decoded the same way ingestion compares it."""
    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            rows = cursor.execute("SELECT file_path, hash FROM document").fetchall()
    return {row["file_path"]: _document_hash_text(row["hash"]) for row in rows}


def insert_document(cursor, version: str, hash: str, file_path: str) -> int:
    """Upsert a document row by file_path and return its doc_id."""
    res = cursor.execute(
        """
        INSERT INTO document (current_version, hash, file_path)
        VALUES (%s, %s, %s)
        ON CONFLICT (file_path)
        DO UPDATE SET current_version = EXCLUDED.current_version, hash = EXCLUDED.hash
        RETURNING doc_id
        """,
        (version, hash, file_path),
    ).fetchone()

    return res["doc_id"]


def resolve_immediate_heading(
    cursor, chunk: RawChunk, doc_id: int, heading_cache: dict[tuple, int]
) -> int | None:
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
                (text, level, doc_id, parent_id),
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
            (content, metadata, dc_type, document_source,
             lexical_embedding, semantic_embedding, closest_heading)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (content, metadata, dc_type, document_source, closest_heading) DO UPDATE
            SET lexical_embedding = EXCLUDED.lexical_embedding,
                semantic_embedding = EXCLUDED.semantic_embedding
        RETURNING chunk_id
        """,
        (
            chunk.text,
            "{}",
            chunk.kind,
            chunk.source,
            f"{sparse}/30522" if sparse else None,
            dense,
            heading_id,
        ),
    )


def _clear_sources(cursor, sources: list[str], keep: bool) -> None:
    """Delete indexed chunks/headings/documents for `sources` (keep=False) or for
    everything *except* `sources` (keep=True).

    Re-ingesting must replace a document, not append to it: the uniqueness
    constraints on heading/document_chunks include nullable columns, and NULLs
    never conflict, so a plain re-insert duplicated every chunk on each run.
    """
    match = "<> ALL(%s)" if keep else "= ANY(%s)"
    if cursor.execute("SELECT to_regclass('response_sources') AS t").fetchone()["t"]:
        cursor.execute(
            f"""
            DELETE FROM response_sources WHERE doc_chunks_id IN
                (SELECT chunk_id FROM document_chunks WHERE document_source {match})
            """,
            (sources,),
        )
    cursor.execute(f"DELETE FROM document_chunks WHERE document_source {match}", (sources,))
    cursor.execute(
        f"""
        DELETE FROM heading WHERE document_id IN
            (SELECT doc_id FROM document WHERE file_path {match})
        """,
        (sources,),
    )
    if keep:
        cursor.execute(f"DELETE FROM document WHERE file_path {match}", (sources,))


def prune_documents(keep_paths: list[str]) -> None:
    """Delete indexed documents whose file_path is not in keep_paths.

    keep_paths is every markdown file still on disk. Unchanged files belong in
    that list so their document, heading, and chunk rows stay.
    """
    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            _clear_sources(cursor, keep_paths, keep=True)
            connection.commit()


def _write_embeddings(
    chunks: list[RawChunk],
    dense_embeddings: list[list[float]],
    sparse_embeddings: list[dict[str, float]],
    prune: bool = False,
    document_hashes: dict[str, str] | None = None,
    keep_paths: list[str] | None = None,
) -> None:
    """Write chunks, replacing each written document's previous rows.

    prune=True deletes indexed documents whose file_path is outside keep_paths.
    keep_paths defaults to the documents being written. A full-corpus run passes
    every file still on disk, including files skipped because their hash matched,
    so those rows and chunks are kept. Only a full-corpus run may prune.
    document_hashes maps each written source path to the file's SHA-256 hex digest,
    stored on document.hash. Callers that omit it leave the hash empty.
    """
    doc_chunks: dict[str, list[dict[str, list | RawChunk]]] = defaultdict(list)

    # Group chunks, dense and sparse embeddings together using source document as key
    for i in range(len(chunks)):
        doc_chunks[chunks[i].source].append(
            {"chunk": chunks[i], "dense": dense_embeddings[i], "sparse": sparse_embeddings[i]}
        )

    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            # tables come from the Alembic migrations (`make migrate`), not from here
            heading_cache = {}

            # in one transaction: optionally drop documents no longer collected (e.g.
            # newly excluded dirs), then replace each written document's chunks/headings
            sources = list(doc_chunks)
            if prune:
                # files still on disk, not merely the files being rewritten
                retained = sources if keep_paths is None else keep_paths
                _clear_sources(cursor, retained, keep=True)
            _clear_sources(cursor, sources, keep=False)

            # insert document into table
            for doc in doc_chunks:
                digest = document_hashes[doc] if document_hashes is not None else b""
                doc_id = insert_document(cursor=cursor, version=1, hash=digest, file_path=doc)
                for chunk_group in doc_chunks[doc]:
                    insert_chunk(
                        cursor=cursor, data=chunk_group, doc_id=doc_id, heading_cache=heading_cache
                    )

            connection.commit()


def embed_and_index(
    chunks: list[RawChunk],
    prune: bool = False,
    document_hashes: dict[str, str] | None = None,
    keep_paths: list[str] | None = None,
) -> None:  # pragma: no cover - integration
    """Embed `chunks` and write them, replacing their documents' existing rows.

    prune=True deletes documents missing from keep_paths. The pipeline passes
    every file still on disk so unchanged documents are kept. document_hashes,
    when given, is stored on each written document row as its SHA-256 hex digest.
    """
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

    _write_embeddings(
        chunks=chunks,
        dense_embeddings=dense_embeddings,
        sparse_embeddings=sparse_embeddings,
        prune=prune,
        document_hashes=document_hashes,
        keep_paths=keep_paths,
    )


def populate_alarms(alarms_json: dict) -> None:
    """Upsert the alarm catalogue from an alarms file (see ingestion/seed_alarms.py).

    Codes are "<origin>.<module>.<sequence>"; the module part must be listed in
    `_modules`. Raises InvalidInputError on the first malformed alarm, before its
    row is written; the connection opens first, so this needs a reachable database.
    """
    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            # use _modules to populate alarm_module table first
            for module in alarms_json["_modules"]:
                cursor.execute(
                    """
                    INSERT INTO alarm_module (code, title)
                    VALUES (%s, %s)
                    ON CONFLICT (code, title) DO UPDATE 
                    SET title = EXCLUDED.title
                    """,
                    (module, alarms_json["_modules"][module]),
                )

            # populate individual alarms
            for alarm in alarms_json["alarms"]:
                code_sections = alarm["code"].split(settings.alarm_delim)

                if len(code_sections) != 3:
                    raise InvalidInputError(["code"])

                invalid_fields = []

                alarm_data = {
                    # alarm_code data
                    "origin": code_sections[0],
                    "sequence": code_sections[2],
                    "title": alarm["title"],
                    "severity_score": alarm["severity"],  # added separate severity score (int)
                    "severity_category": alarm[
                        "severity_category"
                    ].lower(),  # severity category (enum)
                    "alarm_text": alarm["alarm_text"],
                    "data_fields": alarm["data_fields"],
                    # alarm_module data
                    "code": code_sections[1],
                    "module_title": alarm["domain"],
                }

                # Validate inputs
                if alarm_data["severity_category"].lower() not in VALID_SEVERITY:
                    invalid_fields.append("severity_category")

                if not alarm_data["module_title"]:
                    invalid_fields.append("domain")

                if alarm_data["severity_score"] <= 0:
                    invalid_fields.append("severity")

                if not alarm_data["title"]:
                    invalid_fields.append("title")

                if not alarm_data["alarm_text"]:
                    invalid_fields.append("alarm_test")

                if not (alarm_data["origin"] and alarm_data["code"] and alarm_data["sequence"]):
                    invalid_fields.append("code")

                # stop processing and raise error if input is malformed/invalid
                if invalid_fields:
                    raise InvalidInputError(invalid_fields)

                # insert alarm module, ignore on conflict
                module_res = cursor.execute(
                    """
                    SELECT id FROM alarm_module
                    WHERE code = %s AND title = %s;
                    """,
                    (alarm_data["code"], alarm_data["module_title"]),
                ).fetchone()

                # insert alarm code, update details on conflict
                cursor.execute(
                    """
                    INSERT INTO alarm_code
                    (origin, alarm_sequence, title, severity_score, severity_category,
                     alarm_text, data_fields, module)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (origin, alarm_sequence, module) DO UPDATE 
                        SET title = EXCLUDED.title,
                            severity_score = EXCLUDED.severity_score,
                            severity_category = EXCLUDED.severity_category,
                            alarm_text = EXCLUDED.alarm_text,
                            data_fields = EXCLUDED.data_fields; 
                    """,
                    (
                        alarm_data["origin"],
                        alarm_data["sequence"],
                        alarm_data["title"],
                        alarm_data["severity_score"],
                        alarm_data["severity_category"],
                        alarm_data["alarm_text"],
                        Jsonb(alarm_data["data_fields"]),
                        module_res["id"],
                    ),
                )

            connection.commit()


def populate_keyword_table(specificity_threshold: float = 25.0) -> None:
    """Rebuild keyword_lookup: domain terms -> the chunks that mention them + IDF.

    Candidate terms are inline code, ALL-CAPS identifiers and ordinary words from
    text/table/list chunks. A term is kept if it is structural (code/acronym) or at
    least `specificity_threshold` times more frequent in the docs than in general
    English (wordfreq); terms in over 25% of chunks are too common and skipped.
    """
    TOKEN_RE = re.compile(
        r"`([^`\n]{2,40})`"  # .md inline code ` `
        r"|(\b[A-Z]{2,}[A-Z0-9_-]*\b)"  # ALL_CAPS acronyms/codes
        r"|(\b[A-Za-z]{3,35}\b)"  # Standard words
    )

    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            res = cursor.execute("""
                SELECT chunk_id, content FROM document_chunks
                WHERE dc_type = 'text' OR dc_type = 'table' OR dc_type = 'list';
            """).fetchall()

            term_to_chunks = defaultdict(set)
            structural_terms = set()
            total_tokens = 0
            total_chunks = len(res)

            for entry in res:
                for match in TOKEN_RE.finditer(entry["content"]):
                    raw_token = next(g for g in match.groups() if g is not None)
                    term = raw_token.lower().strip()
                    if len(term) < 2:
                        continue

                    term_to_chunks[term].add(entry["chunk_id"])
                    total_tokens += 1

                    # mark allcaps and inline code as domain specific
                    if match.lastindex in (1, 2):
                        structural_terms.add(term)

            # compute IDF weights
            payload = []
            for term, chunk_set in term_to_chunks.items():
                doc_freq = len(chunk_set)
                # skip terms appearing in >25% of chunks
                if doc_freq > max(5, int(total_chunks * 0.25)):
                    continue

                # calculate domain specificity
                corpus_prob = doc_freq / max(1, total_tokens)
                english_prob = word_frequency(term, "en", minimum=1e-9)
                specificity = corpus_prob / english_prob

                # keep if it's a structural/code identifier OR high domain specificity
                if term in structural_terms or specificity >= specificity_threshold:
                    idf = math.log(1.0 + (total_chunks / float(doc_freq)))
                    sorted_chunks = sorted(chunk_set)
                    payload.append((term, sorted_chunks, idf))

            # insert all entries. psycopg 3 has no psycopg2-style `VALUES %s` bulk
            # expansion (it saw 1 placeholder vs thousands of params); executemany
            # batches the rows in a pipeline instead
            cursor.executemany(
                """
                INSERT INTO keyword_lookup (keyword, related_chunks, idf_weight)
                VALUES (%s, %s, %s)
                ON CONFLICT (keyword) DO UPDATE
                SET related_chunks = EXCLUDED.related_chunks,
                    idf_weight = EXCLUDED.idf_weight;
            """,
                payload,
            )

            # re-ingest replaces chunks (new chunk_ids), so terms that weren't
            # re-emitted would keep pointing at chunks that no longer exist
            cursor.execute(
                "DELETE FROM keyword_lookup WHERE keyword <> ALL(%s)",
                ([term for term, _, _ in payload],),
            )

            connection.commit()
