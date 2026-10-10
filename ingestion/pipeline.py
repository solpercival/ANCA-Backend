"""Ingestion entrypoint: docs submodule -> chunk -> embed -> pgvector.

Run offline (make ingest / scheduled job / on docs-submodule bump), not in the
serving path. Model-backed embedding is imported lazily.

Order of a full run: seed the alarm catalogue, hash each markdown file, and
compare that digest with document.hash. Files whose hash is missing or different
are chunked and embedded, replacing their previous rows. Files with the same
hash stay as they are, including their chunks. Documents whose files disappeared
are pruned. keyword_lookup is rebuilt when any file was re-embedded or pruned.
The tables must already exist: `make ingest` applies the Alembic migrations first.
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

    Hashes the bytes on disk, not the chunk text. Ingestion compares this digest
    with document.hash to decide whether the file needs re-embedding.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_markdown_files(docs_dir: Path) -> dict[str, str]:
    """SHA-256 hex digest of each collected markdown file, keyed by chunk source path."""
    return {str(path): hash_file(path) for path in iter_markdown_files(docs_dir)}


def changed_document_hashes(current: dict[str, str], stored: dict[str, str]) -> dict[str, str]:
    """Digests that are missing from the database or differ from document.hash.

    An empty stored hash counts as different, so rows written before hashing
    was stored are re-embedded once.
    """
    return {path: digest for path, digest in current.items() if stored.get(path) != digest}


def collect_markdown(docs_dir: Path, sources: set[str] | None = None) -> list[RawChunk]:
    """Chunk collected markdown files; each chunk's source is its file path.

    sources, when given, limits chunking to those paths. Unchanged files are
    omitted so they are not embedded again.
    """
    # lazy: the chunker pulls in the tokenizer stack
    from ingestion.chunker import chunk_markdown

    chunks: list[RawChunk] = []
    for path in iter_markdown_files(docs_dir):
        source = str(path)
        if sources is not None and source not in sources:
            continue
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), source=source))
    return chunks


def run(docs_dir: str = "docs") -> int:  # pragma: no cover - integration
    """Ingest docs_dir. Returns how many chunks were re-embedded."""
    docs_path = Path(docs_dir)
    current_hashes = hash_markdown_files(docs_path)
    # Lazy import keeps hosted CI free of torch.
    from ingestion.indexers import (
        embed_and_index,
        load_document_hashes,
        populate_keyword_table,
        prune_documents,
    )
    from ingestion.seed_alarms import seed

    seed()
    stored = load_document_hashes()
    changed = changed_document_hashes(current_hashes, stored)
    removed = [path for path in stored if path not in current_hashes]
    chunks = collect_markdown(docs_path, set(changed)) if changed else []
    # keep_paths is every file still on disk, including ones whose hash matched
    keep_paths = list(current_hashes)

    if chunks:
        embed_and_index(
            chunks,
            prune=True,
            document_hashes=changed,
            keep_paths=keep_paths,
        )
    elif removed:
        prune_documents(keep_paths)

    if chunks or removed:
        populate_keyword_table()  # DROP this line + the import if v2 no longer defines it

    skipped = len(current_hashes) - len(changed)
    print(
        f"indexed {len(chunks)} chunks from {len(changed)} changed files, "
        f"skipped {skipped} unchanged, pruned {len(removed)} missing",
        flush=True,
    )
    return len(chunks)


if __name__ == "__main__":  # pragma: no cover
    run()
