"""Chunks keep their place in the document: the heading path is embedded and
reranked with the text, content-free pieces are dropped at ingestion, and the
generator is shown a selected chunk's whole section.
"""

import ingestion.indexers as indexers
import ingestion.pipeline as pipeline
import pytest
from ingestion.chunker import RawChunk, chunk_markdown

from rag_engine.api.schemas import EffortSettings, ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.config import get_settings
from rag_engine.orchestrator import Orchestrator
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.retrieval.reranker import Qwen3Reranker
from tests.fakes import FakeAlarmStore, FakePreprocessor

FIRMWARE_PAGE = """# Device firmware upgrade
AMCore supports uploading firmware to EtherCAT devices.

## Prerequisites

* The firmware binary file must be accessible on disk.
* The fieldbus must be in INIT or PREOP state.

### AMCore device mode
Start AMCore in device mode:

```bat
AMCore.exe -start device
```

This brings the fieldbus to PREOP.
"""


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --- ingestion ---------------------------------------------------------------


def test_chunk_cut_out_of_a_section_carries_its_heading_path():
    chunks = chunk_markdown(FIRMWARE_PAGE, "firmware.md")

    prerequisites = next(c for c in chunks if c.kind == "list")
    assert "Prerequisites" not in prerequisites.text
    assert prerequisites.heading_path == "Device firmware upgrade > Prerequisites"
    assert prerequisites.context_text == (
        "Device firmware upgrade > Prerequisites\n" + prerequisites.text
    )


def test_heading_only_and_blank_pieces_are_not_chunks():
    """'## Prerequisites' is followed directly by a list, which is cut out as its
    own chunk; the bare heading left behind says nothing by itself."""
    chunks = chunk_markdown(FIRMWARE_PAGE, "firmware.md")

    assert all(c.text.strip() for c in chunks)
    assert not any(c.text.strip() == "## Prerequisites" for c in chunks)
    # nothing with content is lost
    text = "\n".join(c.text for c in chunks)
    for kept in ("uploading firmware", "INIT or PREOP", "-start device", "brings the fieldbus"):
        assert kept in text
    # a heading followed by text stays in that text's chunk
    assert any(c.text.startswith("### AMCore device mode") for c in chunks)


def test_label_stays_with_the_block_it_introduces():
    """'**Rules:**' alone is embedded as little more than its heading path, and the
    list after it does not say what it lists."""
    page = (
        "## M-Code Modes\n\n"
        "A mode 4 M-Code calls a subprogram.\n\n"
        "1. Lookahead is broken by mode 4 M-Codes.\n\n"
        "**Rules:**\n\n"
        "1. Only one mode 4 M-Code per block.\n\n"
        "---\n"
    )

    chunks = chunk_markdown(page, "mcodes.md")

    assert [c.kind for c in chunks] == ["list", "list"]
    # compared word by word: the header splitter rewrites the blank lines between blocks
    assert chunks[0].text.split() == (
        "## M-Code Modes A mode 4 M-Code calls a subprogram. "
        "1. Lookahead is broken by mode 4 M-Codes."
    ).split()
    assert chunks[1].text.split() == "**Rules:** 1. Only one mode 4 M-Code per block.".split()
    assert not any("---" in c.text for c in chunks)


def test_chunk_without_headings_is_embedded_as_its_text():
    chunk = RawChunk(text="plain paragraph", source="a.md")

    assert chunk.heading_path == ""
    assert chunk.context_text == "plain paragraph"


def test_dense_embedding_input_is_the_text_under_its_heading_path():
    sent = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"embeddings": [[0.0]] * len(sent[-1])}

    class FakeClient:
        def post(self, url, json):
            sent.append(json["input"])
            return FakeResponse()

    chunk = RawChunk(
        text="* The fieldbus must be in INIT or PREOP state.",
        source="firmware.md",
        headers={"h1": "Device firmware upgrade", "h2": "Prerequisites"},
        kind="list",
    )

    indexers._dense_embed([chunk], FakeClient())

    assert sent == [[chunk.context_text]]
    assert sent[0][0].startswith("Device firmware upgrade > Prerequisites\n")


def test_chunking_version_is_part_of_the_file_hash(tmp_path, monkeypatch):
    """Otherwise a change to the chunker would skip every file as unchanged."""
    path = tmp_path / "doc.md"
    path.write_text("# Title\nbody\n", encoding="utf-8")
    before = pipeline.hash_file(path)

    monkeypatch.setattr(pipeline, "CHUNKING_VERSION", pipeline.CHUNKING_VERSION + 1)

    assert pipeline.hash_file(path) != before


# --- reranking ---------------------------------------------------------------


def test_retrieved_chunk_context_text_uses_the_stored_heading_path():
    with_path = Chunk(
        chunk_id="1",
        text="* The fieldbus must be in INIT or PREOP state.",
        source="firmware.md",
        metadata={"heading_path": "Device firmware upgrade > Prerequisites"},
    )
    without_path = Chunk(chunk_id="2", text="older chunk", source="a.md")

    assert with_path.context_text == (
        "Device firmware upgrade > Prerequisites\n* The fieldbus must be in INIT or PREOP state."
    )
    assert without_path.context_text == "older chunk"


async def test_reranker_scores_the_chunk_under_its_heading_path():
    seen = []
    reranker = Qwen3Reranker(min_score=0.0, relative_min=0.0, min_keep=1)
    reranker._ensure_loaded = lambda: None  # type: ignore[method-assign]

    def score(query, texts):
        seen.extend(texts)
        return [0.5] * len(texts)

    reranker._score = score  # type: ignore[method-assign]
    chunk = Chunk(
        chunk_id="1",
        text="* The fieldbus must be in INIT or PREOP state.",
        source="firmware.md",
        metadata={"heading_path": "Device firmware upgrade > Prerequisites"},
    )

    result = await reranker.rerank(
        "firmware mismatch", [chunk], effort=EffortSettings(reranker_n=5)
    )

    assert seen == [chunk.context_text]
    # the chunk itself is unchanged: its text is what gets cited and quoted
    assert result[0].text == "* The fieldbus must be in INIT or PREOP state."


# --- section context for the generator ---------------------------------------


class FakeSectionStore:
    """chunk id -> (section id, section text); `calls` records the ids asked for."""

    def __init__(self, sections=None, fail=False):
        self._sections = sections or {}
        self._fail = fail
        self.calls = []

    async def section_texts(self, chunk_ids):
        self.calls.append(list(chunk_ids))
        if self._fail:
            raise RuntimeError("db down")
        return {i: self._sections[i] for i in chunk_ids if i in self._sections}


class FakeRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    async def retrieve(self, query, top_k, where=None):
        return self._chunks


class FakeReranker:
    async def rerank(self, query, chunks, effort):
        return chunks[: effort.reranker_n]


class RecordingGenerator:
    def __init__(self, answer):
        self._answer = answer
        self.prompts = []

    async def generate(self, prompt, tokens=None, thinking=False):
        self.prompts.append(prompt)
        return self._answer


def _chunk(chunk_id, text, section="Section"):
    return Chunk(chunk_id=chunk_id, text=text, source="manual.md", score=0.9, section=section)


def _orchestrator(chunks, sections, generator=None):
    return Orchestrator(
        FakePreprocessor(),
        FakeRetriever(chunks),
        FakeReranker(),
        generator or RecordingGenerator("COVERAGE: full\nRestart the drive."),
        FakeAlarmStore(),
        section_store=sections,
    )


async def test_selected_chunk_is_widened_to_its_whole_section():
    chunks = [_chunk("1", "Start AMCore in device mode:")]
    section = "Start AMCore in device mode:\n\nAMCore.exe -start device\n\nThis brings it to PREOP."
    orch = _orchestrator(chunks, FakeSectionStore({"1": ("h7", section)}))

    context = await orch._section_context(chunks, "am.fb.0004")

    assert [c.text for c in context] == [section]
    assert (context[0].chunk_id, context[0].source, context[0].section) == (
        "1",
        "manual.md",
        "Section",
    )
    # the ranked chunk is left as it was
    assert chunks[0].text == "Start AMCore in device mode:"


async def test_chunks_of_one_section_become_a_single_block():
    chunks = [
        _chunk("1", "Start AMCore in device mode:"),
        _chunk("2", "unrelated", section="Other"),
        _chunk("3", "AMCore.exe -start device"),
    ]
    section = "Start AMCore in device mode:\n\nAMCore.exe -start device"
    store = FakeSectionStore({"1": ("h7", section), "3": ("h7", section)})

    context = await _orchestrator(chunks, store)._section_context(chunks, "am.fb.0004")

    assert [c.text for c in context] == [section, "unrelated"]


async def test_long_section_stays_as_the_selected_chunk(monkeypatch):
    monkeypatch.setenv("CONTEXT_SECTION_MAX_CHARS", "50")
    chunks = [_chunk("1", "one row of a long table")]
    store = FakeSectionStore({"1": ("h7", "x" * 51)})

    context = await _orchestrator(chunks, store)._section_context(chunks, "am.cfg.0001")

    assert [c.text for c in context] == ["one row of a long table"]


async def test_sections_stop_being_added_when_the_context_is_full(monkeypatch):
    monkeypatch.setenv("CONTEXT_MAX_CHARS", "60")
    chunks = [_chunk("1", "a" * 10), _chunk("2", "b" * 10)]
    store = FakeSectionStore({"1": ("h1", "A" * 40), "2": ("h2", "B" * 40)})

    context = await _orchestrator(chunks, store)._section_context(chunks, "am.fb.0004")

    # the best-ranked chunk gets its section (40 + 10 = 50); the second would make 80
    assert [c.text for c in context] == ["A" * 40, "b" * 10]


async def test_section_context_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("CONTEXT_SECTION_MAX_CHARS", "0")
    chunks = [_chunk("1", "piece")]
    store = FakeSectionStore({"1": ("h7", "the whole section")})

    context = await _orchestrator(chunks, store)._section_context(chunks, "am.fb.0004")

    assert context == chunks
    assert store.calls == []


async def test_section_lookup_failure_falls_back_to_the_chunks():
    chunks = [_chunk("1", "piece")]

    context = await _orchestrator(chunks, FakeSectionStore(fail=True))._section_context(
        chunks, "am.fb.0004"
    )

    assert context == chunks


async def test_without_a_section_store_the_chunks_are_used_as_they_are():
    chunks = [_chunk("1", "piece")]

    assert await _orchestrator(chunks, None)._section_context(chunks, "am.fb.0004") == chunks


async def test_resolve_shows_the_generator_the_section_and_grounds_causes_in_it():
    chunks = [_chunk("1", "Start AMCore in device mode:", section="AMCore device mode")]
    section = (
        "Start AMCore in device mode:\n\n"
        "Uploads are rejected when the fieldbus has already reached the OP state."
    )
    generator = RecordingGenerator(
        "COVERAGE: full\n"
        "Start AMCore in device mode before uploading.\n"
        "CAUSE: Uploads are rejected when the fieldbus has already reached the OP state."
    )
    orch = _orchestrator(chunks, FakeSectionStore({"1": ("h7", section)}), generator)

    resp = await orch.resolve(ResolveRequest(code="am.fb.0002"), Tier.technician)

    assert section in generator.prompts[0]
    # the cause sentence is only in the widened section, not in the selected chunk
    assert resp.likely_causes == [
        "Uploads are rejected when the fieldbus has already reached the OP state."
    ]
    # citations still come from the ranked chunk
    assert [c.section for c in resp.citations] == ["AMCore device mode"]
