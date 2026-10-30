"""Structure-aware markdown chunking (offline).

Splits on headers while keeping code blocks, tables, and lists atomic. This is
the documentation team's territory: it runs during ingestion, never per request.

A piece cut out of a section (a list, table or code block) no longer contains its
heading, so on its own it does not say what it is about: "The fieldbus must be in
INIT or PREOP" matched an EtherCAT state alarm as well as the firmware page it
came from. Each chunk therefore carries its heading path (RawChunk.heading_path),
which is embedded and reranked together with the text (RawChunk.context_text).
"""

import hashlib
import json
import re
from dataclasses import dataclass, field

from langchain_text_splitters import MarkdownHeaderTextSplitter

SPLIT_HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")]
# Blocks cut out of a section into their own chunk (kind = the key), applied in
# this order. Note the heading text stays only in the section's first piece.
ATOMIC_BLOCKS = {
    "table": re.compile(r"(?:^\|.*\|\s*$\n?)+", re.MULTILINE),
    "code": re.compile(r"```.*?```", re.DOTALL),
    "list": re.compile(r"(?:^\s*(?:[-*+]|\d+\.)\s+.+$\n?)+", re.MULTILINE),
}
# positions in the (kind, text, headers_json) segment tuples used while splitting
IDX_TAG = 0
IDX_TEXT = 1
IDX_HEADERS = 2

# a markdown heading line; a piece made only of these (and blank lines) has no content
HEADING_LINE = re.compile(r"^\s*#{1,6}\s.*$", re.MULTILINE)
# a horizontal rule on its own line: layout, not content
HORIZONTAL_RULE = re.compile(r"^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*$\n?", re.MULTILINE)
# A text piece this short (headings not counted) that is followed by a table, code
# block or list is that block's label ("**Rules:**", "Start AMCore in device mode:")
# and is kept with it instead of becoming a chunk of its own.
LABEL_MAX_CHARS = 100
# separates the headings in RawChunk.heading_path, outermost first
HEADING_PATH_SEPARATOR = " > "

HEADER_SPLITTER = MarkdownHeaderTextSplitter(headers_to_split_on=SPLIT_HEADERS, strip_headers=False)


@dataclass
class RawChunk:
    """A chunk before embedding. headers maps level ("h1".."h4") to heading text;
    kind is text | table | code | list (the CHUNK_TYPE enum)."""

    text: str
    source: str
    headers: dict[str, str] = field(default_factory=dict)
    kind: str = "text"

    @property
    def header_cascade(self) -> list[tuple[str, str]]:
        """(level, heading) pairs from outermost to innermost."""
        return sorted(
            ((lvl, txt) for lvl, txt in self.headers.items() if lvl.startswith("h")),
            key=lambda pair: int(pair[0][1:]),
        )

    @property
    def heading_path(self) -> str:
        """The headings above the chunk, outermost first, e.g. "Device firmware
        upgrade > Prerequisites"; "" when it has none."""
        return HEADING_PATH_SEPARATOR.join(text for _, text in self.header_cascade)

    @property
    def context_text(self) -> str:
        """What gets embedded: the text under its heading path, so the vector says
        where the chunk belongs as well as what it says. The stored content stays
        `text` alone."""
        path = self.heading_path
        return f"{path}\n{self.text}" if path else self.text

    @property
    def chunk_id(self) -> str:
        """Content hash for local identity; the database assigns its own BIGSERIAL id."""
        return hashlib.sha256(f"{self.source}:{self.text}".encode()).hexdigest()[:16]


def chunk_markdown(text: str, source: str) -> list[RawChunk]:
    """
    Split a markdown document into chunks: one section per h1-h4 heading
    (langchain-text-splitters), then each table, fenced code block and list cut
    out of its section as its own chunk. There is no size limit, so a section or
    block becomes one chunk however long it is. Pieces with no content of their own
    (a bare heading whose body was cut out as a list or table, a horizontal rule,
    or the whitespace left between two blocks) are dropped: the heading lives on in
    the heading path of the section's other chunks. A short label in front of a
    block stays with that block (merge_labels).

    Parameters:
    text - the content of the document as a str
    source - a str representing the path of the source document
    """
    chunks: list[RawChunk] = []
    buf: list[tuple[str, str, str]] = []  # Stored as type, content, headers

    headers_split_text = HEADER_SPLITTER.split_text(text=text)

    # apply splitting using atomic blocks re
    for section in headers_split_text:
        segments = [("text", section.page_content, json.dumps(section.metadata))]
        for k, v in ATOMIC_BLOCKS.items():
            segments = extract_atomic_blocks(text_sections=segments, pattern=v, title=k)

        buf.extend(merge_labels(segments))

    # convert segments into RawChunks
    for segment in buf:
        new_chunk = RawChunk(
            text=segment[IDX_TEXT],
            source=source,
            headers=json.loads(segment[IDX_HEADERS]),
            kind=segment[IDX_TAG],
        )
        chunks.append(new_chunk)

    return chunks


def has_content(text: str) -> bool:
    """False for a piece that is only heading lines and whitespace."""
    return bool(HEADING_LINE.sub("", text).strip())


def merge_labels(segments: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """
    Tidies the pieces of one section: horizontal rules are removed from its text,
    pieces without content are dropped, and a short text piece directly before a
    table, code block or list is joined onto that block (see LABEL_MAX_CHARS). On
    its own such a label is embedded as little more than its heading path, and the
    block it introduces does not say what it lists. The block keeps its kind.
    Returns a list of tuples in same format as the segments parameter.

    Parameters:
    segments - The pieces of a single section, in document order.
        Stored as (tag, text, headers)
    """
    pieces = [
        (tag, HORIZONTAL_RULE.sub("", text) if tag == "text" else text, headers)
        for tag, text, headers in segments
    ]
    pieces = [piece for piece in pieces if has_content(piece[IDX_TEXT])]

    merged: list[tuple[str, str, str]] = []
    label = ""
    for i, (tag, text, headers) in enumerate(pieces):
        introduces_block = i + 1 < len(pieces) and pieces[i + 1][IDX_TAG] != "text"
        content = HEADING_LINE.sub("", text).strip()
        if tag == "text" and introduces_block and len(content) <= LABEL_MAX_CHARS:
            label = text.strip()
            continue
        # lstrip: a list match can start with the blank lines above it
        merged.append((tag, f"{label}\n\n{text.lstrip()}" if label else text, headers))
        label = ""
    return merged


def extract_atomic_blocks(
    text_sections: list[tuple[str, str, str]], pattern: re.Pattern[str], title: str
) -> list[tuple[str, str, str]]:
    """
    Extracts blocks that matches given pattern from text. Extracted blocks are
    tagged with the provided title argument. Segments already extracted (any tag
    other than "text") pass through unchanged.
    Returns a list of tuples in same format as the text_sections parameter.

    Parameters:
    text_sections - A list of tuples containing the blocks of text or markdown objects.
        Stored as (tag, text, headers)
    pattern - A regex pattern object used to detect and split the existing blocks if found
    title - The tag used for the newly separated object
    """
    buffer: list[tuple[str, str, str]] = []

    for text in text_sections:
        last_end = 0
        if text[IDX_TAG] == "text":
            # search text sections to break up
            for match in pattern.finditer(text[IDX_TEXT]):
                # breaks text into separate segments
                if match.start() > last_end:
                    buffer.append(
                        ("text", text[IDX_TEXT][last_end : match.start()], text[IDX_HEADERS])
                    )
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
