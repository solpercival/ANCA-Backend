"""Structure-aware markdown chunking (offline).

Splits on headers while keeping code blocks, tables, and lists atomic. This is
the documentation team's territory: it runs during ingestion, never per request.
"""
import hashlib
from dataclasses import dataclass, field


@dataclass
class RawChunk:
    text: str
    source: str
    headers: list[str] = field(default_factory=list)
    kind: str = "text"

    @property
    def chunk_id(self) -> str:
        return hashlib.sha256(f"{self.source}:{self.text}".encode()).hexdigest()[:16]


def chunk_markdown(text: str, source: str) -> list[RawChunk]:
    """Minimal splitter: section by top-level headers, keep fenced code atomic.

    Real implementation uses the langchain markdown splitters; this keeps the
    pipeline importable and testable without extra deps.
    """
    chunks: list[RawChunk] = []
    buf: list[str] = []
    in_code = False

    def flush() -> None:
        joined = "\n".join(buf).strip()
        if joined:
            chunks.append(RawChunk(text=joined, source=source))
        buf.clear()

    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        if line.startswith("#") and not in_code:
            flush()
        buf.append(line)
    flush()
    return chunks
