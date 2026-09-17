"""Ingestion entrypoint: docs submodule -> chunk -> embed -> pgvector.

Run offline (make ingest / scheduled job / on docs-submodule bump), not in the
serving path. Model-backed embedding is imported lazily.
"""
from pathlib import Path

from ingestion.chunker import RawChunk, chunk_markdown


def collect_markdown(docs_dir: Path) -> list[RawChunk]:
    chunks: list[RawChunk] = []
    for path in sorted(docs_dir.rglob("*.md")):
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), source=str(path)))
    return chunks


def run(docs_dir: str = "docs") -> int:  # pragma: no cover - integration
    chunks = collect_markdown(Path(docs_dir))
    # Lazy import keeps hosted CI free of torch.
    from ingestion.indexers import embed_and_index

    embed_and_index(chunks)
    return len(chunks)


if __name__ == "__main__":  # pragma: no cover
    n = run()
    print(f"indexed {n} chunks")
