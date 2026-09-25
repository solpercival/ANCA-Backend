"""Ingestion entrypoint: docs submodule -> chunk -> embed -> pgvector.

Run offline (make ingest / scheduled job / on docs-submodule bump), not in the
serving path. Model-backed embedding is imported lazily.
"""
from pathlib import Path
import json

from ingestion.chunker import RawChunk, chunk_markdown

def collect_markdown(docs_dir: Path) -> list[RawChunk]:
    chunks: list[RawChunk] = []
    for path in sorted(docs_dir.rglob("*.md")):
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), source=str(path)))
    return chunks


def run(docs_dir: str = "docs") -> int:  # pragma: no cover - integration
    chunks = collect_markdown(Path(docs_dir))
    # Lazy import keeps hosted CI free of torch.
    from ingestion.indexers import embed_and_index, populate_alarms, populate_keyword_table
    
    # collect alarms from sample.json (temporary measure for inserting alarms)
    alarm_filepath: str = "docs/docs-proto/starter-kit/alarms/alarms.sample.json"
    with open(alarm_filepath, 'r', encoding='utf-8') as file:
        alarms_json = json.load(file)
  
    populate_alarms(alarms_json)

    embed_and_index(chunks)
    populate_keyword_table()
    return len(chunks)


if __name__ == "__main__":  # pragma: no cover
    n = run()
    print(f"indexed {n} chunks")
