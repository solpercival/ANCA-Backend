"""initial schema: lift-and-shift of scripts/init_pgvector.sql

A statement-for-statement copy of scripts/init_pgvector.sql as of this revision,
so a database built by migrations is identical to one built by the old docker
init script. Nothing is redesigned or "fixed" here (including the keyword_lookup
statements that lack IF NOT EXISTS); schema changes belong in later revisions.

An existing database that was created by init_pgvector.sql already has this
schema: mark it as migrated with `alembic stamp 0001` rather than upgrading.

Revision ID: 0001
Revises:
Create Date: 2026-09-30
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UPGRADE = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    # CREATE TYPE isn't idempotent; ignore the error if the enums already exist
    """
    DO $$ BEGIN
        CREATE TYPE CHUNK_TYPE AS ENUM('table', 'list', 'code', 'text');
        CREATE TYPE SEVERITY AS ENUM('debug', 'info', 'warning', 'error', 'fatal');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$
    """,
    # document
    """
    CREATE TABLE IF NOT EXISTS document (
        doc_id SERIAL PRIMARY KEY,
        current_version VARCHAR(16) NOT NULL,
        hash BYTEA NOT NULL,
        file_path TEXT NOT NULL UNIQUE,
        CONSTRAINT prevent_duplicate_documents UNIQUE(current_version, hash, file_path)
    )
    """,
    # alarm_module
    """
    CREATE TABLE IF NOT EXISTS alarm_module (
        id SERIAL PRIMARY KEY,
        code VARCHAR(6) NOT NULL,
        title VARCHAR(120) NOT NULL,
        CONSTRAINT prevent_duplicate_alarm_module UNIQUE (code, title)
    )
    """,
    # heading
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
    """,
    "CREATE INDEX IF NOT EXISTS fk_heading_document_idx ON heading (document_id)",
    "CREATE INDEX IF NOT EXISTS fk_heading_parent_heading_idx ON heading (parent_heading)",
    # document_chunks
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
        CONSTRAINT prevent_duplicate_chunks UNIQUE(content, metadata, dc_type, document_source, closest_heading),
        CONSTRAINT fk_document_chunks_heading
            FOREIGN KEY (closest_heading)
            REFERENCES heading (heading_id)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    )
    """,
    "CREATE INDEX IF NOT EXISTS fk_document_chunks_heading_idx ON document_chunks (closest_heading)",
    # alarm_code
    """
    CREATE TABLE IF NOT EXISTS alarm_code (
        alarm_code_id SERIAL PRIMARY KEY,
        origin VARCHAR(255) NOT NULL,
        alarm_sequence VARCHAR(255) NOT NULL,
        title VARCHAR(255) NOT NULL,
        severity_score INTEGER NOT NULL,
        severity_category SEVERITY NOT NULL,
        alarm_text VARCHAR(255) NOT NULL,
        data_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
        module INTEGER NOT NULL,
        CONSTRAINT fk_alarm_code_module
            FOREIGN KEY (module)
            REFERENCES alarm_module (id)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION,
        CONSTRAINT prevent_duplicate_alarm_code UNIQUE (origin, alarm_sequence, module)
    )
    """,
    "CREATE INDEX IF NOT EXISTS fk_alarm_code_module_idx ON alarm_code (module)",
    # role + the account tiers (rag_engine.auth.tiers.Tier); users.role_rid maps to these
    """
    CREATE TABLE IF NOT EXISTS role (
        rid INT NOT NULL PRIMARY KEY,
        name VARCHAR(45) NOT NULL
    )
    """,
    """
    INSERT INTO role (rid, name) VALUES
        (1, 'operator'),
        (2, 'technician'),
        (3, 'partner')
    ON CONFLICT (rid) DO NOTHING
    """,
    # users
    """
    CREATE TABLE IF NOT EXISTS users (
        uid SERIAL NOT NULL,
        role_rid INT NOT NULL,
        username VARCHAR(80) NOT NULL,
        password BYTEA NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        PRIMARY KEY (uid),
        CONSTRAINT fk_user_role
            FOREIGN KEY (role_rid)
            REFERENCES role (rid)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    )
    """,
    "CREATE INDEX IF NOT EXISTS fk_user_role_idx ON users (role_rid)",
    "CREATE UNIQUE INDEX IF NOT EXISTS users_username_idx ON users (username)",
    # response
    """
    CREATE TABLE IF NOT EXISTS response (
        response_id BIGSERIAL PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        query VARCHAR(255) NOT NULL,
        response_body TEXT,
        time_generated TIMESTAMP NOT NULL,
        user_feedback BOOLEAN DEFAULT NULL,
        alarm_id INTEGER REFERENCES alarm_code(alarm_code_id) DEFAULT NULL,
        user_uid BIGINT REFERENCES users(uid) DEFAULT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS fk_response_alarm_code_idx ON response (alarm_id)",
    "CREATE INDEX IF NOT EXISTS fk_response_user_idx ON response (user_uid)",
    # response_sources
    """
    CREATE TABLE IF NOT EXISTS response_sources (
        doc_chunks_id BIGINT REFERENCES document_chunks(chunk_id) NOT NULL,
        response_id BIGINT REFERENCES response(response_id) NOT NULL,
        PRIMARY KEY (doc_chunks_id, response_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS fk_document_chunks_supports_response_idx ON response_sources (response_id)",
    "CREATE INDEX IF NOT EXISTS fk_response_references_document_chunk_idx ON response_sources (doc_chunks_id)",
    # keyword_lookup (the SQL script has no IF NOT EXISTS here; mirrored as-is)
    """
    CREATE TABLE keyword_lookup(
        keyword TEXT PRIMARY KEY,
        aliases TEXT[] NOT NULL DEFAULT '{}',
        related_chunks BIGINT[] NOT NULL,
        idf_weight REAL NOT NULL DEFAULT 1.0
    )
    """,
    # exact matching on aliases/synonyms
    "CREATE INDEX idx_kw_aliases_gin ON keyword_lookup USING gin (aliases)",
    # trigram index for substring/typo matching on keywords
    "CREATE INDEX idx_kw_trgm_gin ON keyword_lookup USING gin (keyword gin_trgm_ops)",
    # HNSW index on chunks
    """
    CREATE INDEX IF NOT EXISTS document_chunks_semantic_hnsw ON document_chunks
    USING hnsw (semantic_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
    """,
]

# Reverse dependency order. Indexes, constraints and the role seed rows go with
# their tables.
DOWNGRADE = [
    "DROP TABLE IF EXISTS keyword_lookup",
    "DROP TABLE IF EXISTS response_sources",
    "DROP TABLE IF EXISTS response",
    "DROP TABLE IF EXISTS users",
    "DROP TABLE IF EXISTS role",
    "DROP TABLE IF EXISTS alarm_code",
    "DROP TABLE IF EXISTS document_chunks",
    "DROP TABLE IF EXISTS heading",
    "DROP TABLE IF EXISTS alarm_module",
    "DROP TABLE IF EXISTS document",
    "DROP TYPE IF EXISTS SEVERITY",
    "DROP TYPE IF EXISTS CHUNK_TYPE",
    "DROP EXTENSION IF EXISTS pg_trgm",
    "DROP EXTENSION IF EXISTS vector",
]


def upgrade() -> None:
    for statement in UPGRADE:
        op.execute(statement)


def downgrade() -> None:
    for statement in DOWNGRADE:
        op.execute(statement)
