-- Enable pgvector on first boot. Real schema/migrations live in the app
-- (SQLAlchemy + Alembic) and are owned by the RAG team.
CREATE EXTENSION IF NOT EXISTS vector;
