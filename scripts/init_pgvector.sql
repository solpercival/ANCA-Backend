-- Enable pgvector on first boot. Real schema/migrations live in the app
-- (SQLAlchemy + Alembic) and are owned by the RAG team.

-- Postgres automatically creates indexes for primary keys, but not for foreign keys.
-- We create those indexes here to improve query performance.

CREATE EXTENSION IF NOT EXISTS vector;

-- CREATE TYPE isn't idempotent.
-- CREATE TYPE ... will error if this script ever runs twice against the same database.
-- The below block will create the enum types if they don't exist, and ignore the error if they do.
DO $$ BEGIN
    CREATE TYPE CHUNK_TYPE AS ENUM('table', 'list', 'code', 'text');
	CREATE TYPE SEVERITY AS ENUM('debug', 'info', 'warning', 'error', 'fatal');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- -----------------------------------------------------
-- Table alarm_module
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS alarm_module (
	id SERIAL PRIMARY KEY,
	code VARCHAR(6) NOT NULL,
	title VARCHAR(120) NOT NULL
);

-- -----------------------------------------------------
-- Table document
-- -----------------------------------------------------
-- Storing hashes as binary using the BYTEA data type is optimum
CREATE TABLE IF NOT EXISTS document (
	doc_id SERIAL PRIMARY KEY,
	current_version VARCHAR(16) NOT NULL,
	hash BYTEA NOT NULL,
	file_path VARCHAR(120) NOT NULL UNIQUE
);

-- -----------------------------------------------------
-- Table document_chunks
-- -----------------------------------------------------
-- SERIAL will autoincrement the primary key, BIGSERIAL is used here to allow for a larger number of chunks
CREATE TABLE IF NOT EXISTS document_chunks (
	chunk_id BIGSERIAL PRIMARY KEY,
	content TEXT NOT NULL,
	metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
	dc_type CHUNK_TYPE NOT NULL DEFAULT 'text',
	lexical_embedding sparsevec(30522) NOT NULL,
	semantic_embedding vector(1024) NOT NULL
);

-- -----------------------------------------------------
-- Table alarm_code
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS alarm_code (
	alarm_code_id INTEGER PRIMARY KEY,
	origin VARCHAR(255) NOT NULL,
	alarm_sequence VARCHAR(255) NOT NULL,
	title VARCHAR(255) NOT NULL,
	domain VARCHAR(255) NOT NULL,
	severity_score SEVERITY NOT NULL,
	alarm_text VARCHAR(255) NOT NULL,
	data_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
	module INTEGER NOT NULL,
	CONSTRAINT fk_alarm_code_module
		FOREIGN KEY (module)
		REFERENCES alarm_module (id)
		ON DELETE NO ACTION
		ON UPDATE NO ACTION
);

CREATE INDEX fk_alarm_code_module_idx ON alarm_code (module);

-- -----------------------------------------------------
-- Table heading
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS heading (
	heading_id BIGSERIAL PRIMARY KEY,
	heading_order VARCHAR(45) NOT NULL,
	hierarchy VARCHAR(45) NOT NULL,
	document_id INTEGER NOT NULL,
	CONSTRAINT prevent_duplicate_heading UNIQUE(heading_order, document_id),
  	CONSTRAINT fk_heading_document
		FOREIGN KEY (document_id)
		REFERENCES document (doc_id)
		ON DELETE NO ACTION
		ON UPDATE NO ACTION
);

CREATE INDEX fk_heading_document_idx ON heading (document_id);

-- -----------------------------------------------------
-- Table response
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS response (
	response_id BIGSERIAL PRIMARY KEY,
	query VARCHAR(255) NOT NULL,
	response_body TEXT,
	time_generated TIMESTAMP NOT NULL,
	alarm_id INTEGER REFERENCES alarm_code(alarm_code_id) NOT NULL
);

CREATE INDEX fk_response_alarm_code_idx ON response (alarm_id);
CREATE INDEX fk_response_user_idx ON response (user_uid);

-- -----------------------------------------------------
-- Table chunk_headings
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS chunk_headings (
  heading_id BIGINT NOT NULL,
  chunk_id BIGINT NOT NULL,
  PRIMARY KEY (heading_id, chunk_id),
  CONSTRAINT fk_document_chunks_has_heading
    FOREIGN KEY (heading_id)
    REFERENCES heading (heading_id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_heading_has_document_chunks
    FOREIGN KEY (chunk_id)
    REFERENCES document_chunks (chunk_id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

CREATE INDEX fk_heading_has_document_chunks_document_chunks1_idx ON chunk_headings (chunk_id);
CREATE INDEX fk_heading_has_document_chunks_heading1_idx ON chunk_headings (heading_id);

-- -----------------------------------------------------
-- Table response_sources
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS response_sources (
	doc_chunks_id BIGINT REFERENCES document_chunks(chunk_id) NOT NULL,
	response_id BIGINT REFERENCES response(response_id) NOT NULL,
	PRIMARY KEY (doc_chunks_id, response_id)
);

CREATE INDEX fk_document_chunks_supports_response_idx ON response_sources (response_id);
CREATE INDEX fk_response_references_document_chunk_idx ON response_sources (doc_chunks_id);

-- -----------------------------------------------------
-- Table role
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS role (
  rid INT NOT NULL PRIMARY KEY,
  name VARCHAR(45) NOT NULL
);

-- -----------------------------------------------------
-- Table user
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  uid SERIAL NOT NULL,
  role_rid INT NOT NULL,
  username VARCHAR(80) NOT NULL,
  password BYTEA NOT NULL,
  PRIMARY KEY (uid),
  CONSTRAINT fk_user_role
    FOREIGN KEY (role_rid)
    REFERENCES role (rid)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

CREATE INDEX fk_user_role_idx ON users (role_rid);

-- HNSW index
CREATE INDEX ON document_chunks
USING hnsw (semantic_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64); -- Parameters can be tuned
