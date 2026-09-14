"""Structure-aware markdown chunking (offline).

Splits on headers while keeping code blocks, tables, and lists atomic. This is
the documentation team's territory: it runs during ingestion, never per request.
"""
import hashlib
import re
from dataclasses import dataclass, field
from langchain_text_splitters import MarkdownHeaderTextSplitter, MarkdownTextSplitter

CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
SPLIT_HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")]
# regex objects for markdown
TABLE_BLOCK = re.compile(r"(?:^\|.*\|\s*$\n?)+", re.MULTILINE)
CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
LIST_BLOCK = re.compile(r"(?:^\s*(?:[-*+]|\d+\.)\s+.+$\n?)+", re.MULTILINE)

HEADER_SPLITTER = MarkdownHeaderTextSplitter(headers_to_split_on=SPLIT_HEADERS, strip_headers=True)
TEXT_SPLITTER = MarkdownTextSplitter()

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