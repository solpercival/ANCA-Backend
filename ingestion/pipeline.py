"""Ingestion entrypoint: docs submodule -> chunk -> embed -> pgvector.

Run offline (make ingest / scheduled job / on docs-submodule bump), not in the
serving path. Model-backed embedding is imported lazily.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ingestion.chunker import RawChunk

# Not machine documentation, so never retrievable as grounding: the mock API's
# README/INTERFACE describe canned answers, and alarms/ holds the alarm catalogue
# and curated gold answers (the catalogue is loaded separately by seed_alarms).
EXCLUDED_DIRS = frozenset({"mock-api", "alarms"})


def iter_markdown_files(docs_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(docs_dir.rglob("*.md"))
        if not EXCLUDED_DIRS.intersection(path.relative_to(docs_dir).parts[:-1])
    ]


def collect_markdown(docs_dir: Path) -> list[RawChunk]:
    # lazy: the chunker pulls in the tokenizer stack
    from ingestion.chunker import chunk_markdown

    chunks: list[RawChunk] = []
    for path in iter_markdown_files(docs_dir):
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), source=str(path)))
    return chunks


def run(docs_dir: str = "docs") -> int:  # pragma: no cover - integration
    chunks = collect_markdown(Path(docs_dir))
    # Lazy import keeps hosted CI free of torch.
    from ingestion.indexers import embed_and_index
    from ingestion.seed_alarms import seed

    seed()
    # full corpus: prune removes documents that are no longer collected
    embed_and_index(chunks, prune=True)
    return len(chunks)


if __name__ == "__main__":  # pragma: no cover
    n = run()
    print(f"indexed {n} chunks")
