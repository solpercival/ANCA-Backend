"""Ingestion entrypoint: docs submodule -> chunk -> embed -> pgvector.

Run offline (make ingest / scheduled job / on docs-submodule bump), not in the
serving path. Model-backed embedding is imported lazily.

Order of a full run: seed the alarm catalogue, chunk + embed every markdown file
(replacing each document's previous rows, storing that file's SHA-256 hex digest
on document.hash, and pruning documents that disappeared), then rebuild the
keyword lookup table used by query rewriting. The tables must already exist:
`make ingest` applies the Alembic migrations first.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ingestion.chunker import RawChunk

# Not machine documentation, so never retrievable as grounding: the mock API's
# README/INTERFACE describe canned answers, and alarms/ holds the alarm catalogue
# and curated gold answers (the catalogue is loaded separately by seed_alarms).
EXCLUDED_DIRS = frozenset({"mock-api", "alarms"})


def iter_markdown_files(docs_dir: Path) -> list[Path]:
    """Every .md file under docs_dir, sorted, skipping EXCLUDED_DIRS at any depth."""
    return [
        path
        for path in sorted(docs_dir.rglob("*.md"))
        if not EXCLUDED_DIRS.intersection(path.relative_to(docs_dir).parts[:-1])
    ]


def hash_file(path: Path) -> str:
    """SHA-256 hex digest of the file's raw bytes.

    Hashes the bytes on disk, not the chunk text. Later ingestion can compare
    this digest with document.hash to decide whether the file needs re-embedding.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_markdown_files(docs_dir: Path) -> dict[str, str]:
    """SHA-256 hex digest of each collected markdown file, keyed by chunk source path."""
    return {str(path): hash_file(path) for path in iter_markdown_files(docs_dir)}


def collect_markdown(docs_dir: Path) -> list[RawChunk]:
    """Chunk every collected markdown file; each chunk's source is its file path."""
    # lazy: the chunker pulls in the tokenizer stack
    from ingestion.chunker import chunk_markdown

    chunks: list[RawChunk] = []
    for path in iter_markdown_files(docs_dir):
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), source=str(path)))
    return chunks


def run(docs_dir: str = "docs") -> int:  # pragma: no cover - integration
    """Full ingestion of docs_dir; returns the number of chunks indexed."""
    docs_path = Path(docs_dir)
    chunks = collect_markdown(docs_path)
    document_hashes = hash_markdown_files(docs_path)
    # Lazy import keeps hosted CI free of torch.
    from ingestion.indexers import embed_and_index, populate_keyword_table
    from ingestion.seed_alarms import seed

    seed()
    # full corpus: prune removes documents that are no longer collected
    embed_and_index(chunks, prune=True, document_hashes=document_hashes)
    populate_keyword_table()  # DROP this line + the import if v2 no longer defines it
    return len(chunks)


if __name__ == "__main__":  # pragma: no cover
    n = run()
    print(f"indexed {n} chunks")