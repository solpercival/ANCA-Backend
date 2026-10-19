"""Where a chunk came from, in the API contract's terms.

Chunks are stored with the path the ingestion run saw
(docs/docs-proto/starter-kit/docs/user-guide/troubleshoot/coe-device-errors.md).
Clients get {doc, path, section} instead, the shape of doc_refs in the starter
kit's reference-answers.json and of Citation in mock-api/INTERFACE.md:
  path     relative to the documentation bundle's root, so the UI can link to it
  doc      the display name of the document the top-level folder holds
  section  the chunk's heading (Chunk.section; resolved by the stores)
This module is the only place that knows the bundle's root and its document names.
"""

# the documentation bundle's root as ingestion stores it (`make ingest` walks docs/)
DOCS_ROOT = "docs/docs-proto/starter-kit/docs/"

# top-level folder of the bundle -> display name, as used in reference-answers.json
DOC_NAMES = {
    "part-programmers-reference": "Part Programmer's Reference",
    "user-guide": "AMCore User Guide",
}
# for a file outside every named folder (none in the current bundle)
UNKNOWN_DOC = "Documentation"


def doc_path(source: str) -> str:
    """The document's path relative to the bundle root, with forward slashes.

    Strips DOCS_ROOT wherever the stored source has it. A source rooted somewhere
    else (an absolute path, a different checkout location) is cut at its known
    document folder instead, so no local prefix reaches the client either way.
    Anything else is returned as given, minus a leading slash.
    """
    path = source.replace("\\", "/")
    if DOCS_ROOT in path:
        return path.split(DOCS_ROOT, 1)[1]
    for folder in DOC_NAMES:
        if path.startswith(f"{folder}/"):
            return path
        if f"/{folder}/" in path:
            return f"{folder}/" + path.split(f"/{folder}/", 1)[1]
    return path.lstrip("/")


def section_title(heading: str | None) -> str | None:
    """A chunk's heading as plain display text, or None when it has none.

    Headings are stored as written in the markdown ("`G60` — `splineon`"); the
    inline-code backticks are markup, not part of the title. Nothing else is
    changed: underscores and punctuation belong to names like electronic_cam.
    """
    title = " ".join((heading or "").replace("`", "").split())
    return title or None


def doc_name(path: str) -> str:
    """Display name of the document a bundle-relative `path` belongs to: DOC_NAMES
    for a known top-level folder, else that folder's name in title case, or
    UNKNOWN_DOC for a file at the root."""
    folder, sep, _ = path.partition("/")
    if not sep:
        return UNKNOWN_DOC
    return DOC_NAMES.get(folder) or folder.replace("-", " ").replace("_", " ").title()
