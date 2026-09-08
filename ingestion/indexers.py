"""Model-backed embedding + writes to pgvector and the BM25 index.

Imported lazily by pipeline.run so the default (CPU/CI) install never needs it.
"""
from ingestion.chunker import RawChunk


def embed_and_index(chunks: list[RawChunk]) -> None:  # pragma: no cover - GPU path
    raise NotImplementedError(
        "Provided by the ingestion container (Qwen3-Embedding + pgvector + bm25s)."
    )
