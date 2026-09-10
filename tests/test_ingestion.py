from pathlib import Path

import ingestion.indexers as indexers
from ingestion.chunker import chunk_markdown
from ingestion.pipeline import collect_markdown


def test_chunk_markdown_splits_on_headers_and_keeps_content():
    markdown = """# Intro
alpha

## Details
beta

```python
print('hello')
```

# Next
charlie
"""

    chunks = chunk_markdown(markdown, "sample.md")

    assert len(chunks) >= 2
    assert any("Intro" in chunk.text for chunk in chunks)
    assert any("Details" in chunk.text for chunk in chunks)
    assert any("print('hello')" in chunk.text for chunk in chunks)
    assert all(chunk.source == "sample.md" for chunk in chunks)


def test_collect_markdown_reads_nested_markdown_files(tmp_path):
    docs = tmp_path / "docs"
    nested = docs / "nested"
    nested.mkdir(parents=True)

    (docs / "a.md").write_text("# A\nfirst\n", encoding="utf-8")
    (nested / "b.md").write_text("# B\nsecond\n", encoding="utf-8")

    chunks = collect_markdown(docs)

    assert len(chunks) == 2
    texts = {chunk.text for chunk in chunks}
    assert any("# A" in text for text in texts)
    assert any("# B" in text for text in texts)


def test_write_bm25_creates_metadata_and_index(tmp_path, monkeypatch):
    class FakeBM25:
        def __init__(self):
            self.saved = None
            self.corpus = None

        def index(self, tokens):
            self.tokens = tokens

        def save(self, path, corpus=None):
            self.saved = path
            self.corpus = corpus

    fake = FakeBM25()
    monkeypatch.setattr(indexers.bm25s, "BM25", lambda: fake)
    monkeypatch.setattr(indexers.bm25s, "tokenize", lambda corpus: [list(c.split()) for c in corpus])

    chunks = [
        type("Chunk", (), {"text": "first topic", "chunk_id": "a1", "source": "s1"})(),
        type("Chunk", (), {"text": "second topic", "chunk_id": "a2", "source": "s2"})(),
    ]

    target = tmp_path / "bm25-index"
    monkeypatch.setattr(indexers, "get_settings", lambda: type("Settings", (), {"bm25_index_dir": str(target)})())

    indexers._write_bm25(chunks)

    assert target.exists()
    metadata = target.joinpath("metadata.json")
    assert metadata.exists()
    assert "a1" in metadata.read_text(encoding="utf-8")
    assert "a2" in metadata.read_text(encoding="utf-8")
    assert fake.saved == str(target)
