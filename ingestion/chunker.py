"""Structure-aware markdown chunking (offline).

Splits on headers while keeping code blocks, tables, and lists atomic. This is
the documentation team's territory: it runs during ingestion, never per request.
"""
import hashlib
import re
import json
from dataclasses import dataclass, field
from langchain_text_splitters import MarkdownHeaderTextSplitter

SPLIT_HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")]
# regex objects for markdown
ATOMIC_BLOCKS = {
    "table": re.compile(r"(?:^\|.*\|\s*$\n?)+", re.MULTILINE),
    "code": re.compile(r"```.*?```", re.DOTALL),
    "list": re.compile(r"(?:^\s*(?:[-*+]|\d+\.)\s+.+$\n?)+", re.MULTILINE)
}
IDX_CODE = 0
IDX_TEXT = 1
IDX_HEADERS = 2

HEADER_SPLITTER = MarkdownHeaderTextSplitter(headers_to_split_on=SPLIT_HEADERS, strip_headers=False)

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
    """
    Minimal splitter: section by top-level headers, keep fenced code atomic.
    This is a minimal splitter using langchain-text-splitters to split on headers 
    and atomic blocks such as code, lists and tables.

    Parameters:
    text - the content of the document as a str
    source - a str representing the path of the source document
    """
    chunks: list[RawChunk] = []
    buf: list[tuple[str,str,str]] = [] # Stored as type, content, headers

    headers_split_text = HEADER_SPLITTER.split_text(text=text)

    # apply splitting using atomic blocks re
    for section in headers_split_text:
        segments = [("text", section.page_content, json.dumps(section.metadata))]
        for k, v in ATOMIC_BLOCKS.items():
            segments = extract_atomic_blocks(text_sections=segments, pattern=v, title=k)

        buf.extend(segments)

    # convert segments into RawChunks
    for segment in buf:
        new_chunk = RawChunk(text=segment[IDX_TEXT], 
                             source=source, 
                             headers=list(json.loads(segment[IDX_HEADERS]).values()),
                             kind=segment[IDX_CODE])
        chunks.append(new_chunk)

    return chunks

def extract_atomic_blocks(text_sections: list[tuple[str,str,str]],
                          pattern: re.Pattern[str],
                          title: str) -> list[tuple[str,str,str]]:
    buffer: list[tuple[str,str,str]] = []
    """
    Extracts blocks that matches given pattern from text. Extracted blocks are
    tagged with the provided title argument. 
    Returns a list of tuples in same format as the text_sections parameter.
    
    Parameters:
    text_sections - A list of tuples containing the blocks of text or markdown objects. Stored as (tag, text, headers)
    pattern - A regex pattern object used to detect and split the existing blocks if found
    title - The tag used for the newly separated object
    """

    for text in text_sections:
        last_end = 0
        if text[IDX_CODE] == "text":
            # search text sections to break up
            for match in pattern.finditer(text[IDX_TEXT]):
                # breaks text into separate segments
                if match.start() > last_end:
                    buffer.append(("text", text[IDX_TEXT][last_end:match.start()], text[IDX_HEADERS]))
                buffer.append((title, match.group(), text[IDX_HEADERS]))
                last_end = match.end()

            # add remaining text (if necessary)
            if last_end < len(text[IDX_TEXT]):
                buffer.append(("text", text[IDX_TEXT][last_end:], text[IDX_HEADERS]))
        else:
            # ignore non-text sections (i.e. code blocks, tables, etc.)
            buffer.append(text)
        
    # text broken into segments
    return buffer