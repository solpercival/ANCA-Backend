-- Enable pgvector on first boot. Real schema/migrations live in the app
-- (SQLAlchemy + Alembic) and are owned by the RAG team.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE CHUNK_TYPE IF NOT EXISTS AS ENUM('table', 'list', 'code', 'text')
CREATE TYPE SEVERITY IF NOT EXISTS AS ENUM('debug', 'info', 'warning', 'error', 'fatal')

CREATE TABLE IF NOT EXISTS alarm_module (
	id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	code VARCHAR(6) NOT NULL,
	title VARCHAR(120) NOT NULL
)

CREATE TABLE IF NOT EXISTS document (
	doc_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	current_version VARCHAR(16) NOT NULL,
	hash CHAR(64) NOT NULL,
	file_path VARCHAR(120) NOT NULL
)

CREATE TABLE IF NOT EXISTS document_chunks (
	chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	content TEXT NOT NULL,
	metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
	dc_type CHUNK_TYPE NOT NULL DEFAULT 'text',
	document_chunkscol VARCHAR(45) NOT NULL,
	lexical_embedding sparsevec(250002) NOT NULL,
	semantic_embedding vector(1024) NOT NULL
)

CREATE TABLE IF NOT EXISTS alarm_code (
	alarm_code_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	origin VARCHAR(255) NOT NULL,
	alarm_sequence VARCHAR(255) NOT NULL,
	title VARCHAR(255) NOT NULL,
	domain VARCHAR(255) NOT NULL,
	severity_score SEVERITY NOT NULL,
	alarm_text VARCHAR(255) NOT NULL,
	data_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
	module INTEGER REFERENCES alarm_module(id) NOT NULL
)

CREATE TABLE IF NOT EXISTS heading (
	heading_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	order VARCHAR(45) NOT NULL,
	hierarchy VARCHAR(45) NOT NULL,
	document_id INTEGER REFERENCES document(doc_id) NOT NULL
	CONSTRAINT prevent_duplicate_heading UNIQUE(order, document_id)
)

CREATE TABLE IF NOT EXISTS response (
	response_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	query VARCHAR(255) NOT NULL,
	response_body TEXT,
	time_generated TIMESTAMP NOT NULL,
	alarm_id INTEGER REFERENCES alarm_code(alarm_code_id) NOT NULL
)

CREATE TABLE IF NOT EXISTS chunk_headings (
	heading_id BIGINT REFERENCES heading(heading_id) NOT NULL,
	doc_chunks_id BIGINT REFERENCES document_chunks(chunk_id) NOT NULL,
	PRIMARY KEY (heading_id, doc_chunks_id)
)

CREATE TABLE IF NOT EXISTS response_sources (
	doc_chunks_id BIGINT REFERENCES document_chunks(chunk_id) NOT NULL,
	response_id BIGINT REFERENCES response(response_id) NOT NULL,
	PRIMARY KEY (doc_chunks_id, response_id)
)