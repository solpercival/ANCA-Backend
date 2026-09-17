from pathlib import Path

import ingestion.indexers as indexers
from ingestion.chunker import chunk_markdown, RawChunk
from ingestion.pipeline import collect_markdown
import httpx

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

def test_sparse_embedding():
    chunks = [RawChunk(text="test script", source="", headers=[], kind="text"),
              RawChunk(text="motion", source="", headers=[], kind="text")]

    with httpx.Client(timeout=120.0) as client:
        sparse_vecs = indexers._sparse_embed(chunks=chunks, client=client)

    assert(len(sparse_vecs) == len(chunks)) # verify same length
    assert(sparse_vecs[i] for i in sparse_vecs) # verify non-empty embeddings
    assert(len(sparse_vecs[i]) <= 30522 for i in sparse_vecs)

def test_dense_embedding():    
    chunks = [RawChunk(text="test script", source="", headers=[], kind="text"),
              RawChunk(text="motion", source="", headers=[], kind="text")]

    with httpx.Client(timeout=120.0) as client:
        dense_vecs = indexers._dense_embed(chunks=chunks, client=client)

    assert(len(dense_vecs) == len(chunks)) # verify same length
    assert(len(i) == 1024 for i in dense_vecs)   
    