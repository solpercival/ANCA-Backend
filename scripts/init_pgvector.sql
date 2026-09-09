-- Enable pgvector on first boot. Real schema/migrations live in the app
-- (SQLAlchemy + Alembic) and are owned by the RAG team.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
	chunk_id TEXT PRIMARY KEY,
	content TEXT NOT NULL,
	source TEXT NOT NULL,
	metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
	embedding vector NOT NULL
);
