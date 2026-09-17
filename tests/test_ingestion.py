from pathlib import Path

import ingestion.indexers as indexers
from ingestion.chunker import chunk_markdown, RawChunk
from ingestion.pipeline import collect_markdown
from rag_engine.config import get_settings
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

def test_chunk_markdown_splits_code():
    markdown = """
    ## Content
    ```python
    print("hello world!")

    sum = 0
    for i in range(5):
        sum += i
    ```

    Extra text content as text
    """
    chunks = chunk_markdown(markdown, "sample.md")

    assert len(chunks) >= 2
    assert (len(list(filter(lambda x: x.kind == "code", chunks))) == 1)
    assert any("code" == chunk.kind for chunk in chunks)
    assert any("text" == chunk.kind for chunk in chunks)
    assert any("for i in range(5)" in chunk.text for chunk in chunks)
    assert all("Content" in chunk.headers for chunk in chunks)
    assert all(chunk.source == "sample.md" for chunk in chunks)


def test_chunk_markdown_splits_list():
    markdown="""
    ## Content

    ### List 1 (Numbered)
    1. Item A
    2. Item B
    3. Item C

    ### List 2 (Unordered List)
    * alpha
    * beta
        * beta-1
            * beta-1.1
            * beta-1.2
        * beta-2
        * beta-3
    * epsilon
    * zeta
    * gamma
    

    Extra text content as text  
    """
    chunks = chunk_markdown(markdown, "sample.md")
    
    assert len(chunks) >= 3
    assert (len(list(filter(lambda x: x.kind == "list", chunks))) == 2)
    assert any("list" == chunk.kind for chunk in chunks)
    assert any("text" == chunk.kind for chunk in chunks)
    assert any("beta-1" in chunk.text for chunk in chunks)
    assert all("Content" in chunk.headers for chunk in chunks)
    assert any("List 1 (Numbered)" in chunk.headers for chunk in chunks)
    assert all(chunk.source == "sample.md" for chunk in chunks)
    

def test_chunk_markdown_splits_table():
    markdown="""
    ## Content

    ### Table Sample
    | Task ID | Task Description | Priority | Status | Due Date |
    | --- | --- | --- | --- | --- |
    | T-101 | Database Schema Migration | High | In Progress | 2026-06-15 |
    | T-102 | User Authentication API | Critical | Completed | 2026-06-10 |
    | T-103 | Frontend Dashboard Redesign | Medium | Planning | 2026-06-30 |
    | T-104 | Automated Testing Suite | High | Not Started | 2026-07-05 |
    | T-105 | Performance Optimization | Low | On Hold | 2026-07-15 |

    Extra text content as text  
    """
    
    chunks = chunk_markdown(markdown, "sample.md")

    assert len(chunks) >= 2
    assert (len(list(filter(lambda x: x.kind == "table", chunks))) == 1)
    assert any("table" == chunk.kind for chunk in chunks)
    assert any("text" == chunk.kind for chunk in chunks)
    assert any("Task ID" in chunk.text for chunk in chunks)
    assert all("Content" in chunk.headers for chunk in chunks)
    assert any("Table Sample" in chunk.headers for chunk in chunks)
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

    settings = get_settings()
    with httpx.Client(timeout=120.0) as client:
        sparse_vecs = indexers._sparse_embed(chunks=chunks, client=client)

    assert(len(sparse_vecs) == len(chunks)) # verify same length
    assert(sparse_vecs[i] for i in sparse_vecs) # verify non-empty embeddings
    assert(len(sparse_vecs[i]) <= settings.lexical_dim for i in sparse_vecs)

def test_dense_embedding():    
    chunks = [RawChunk(text="test script", source="", headers=[], kind="text"),
              RawChunk(text="motion", source="", headers=[], kind="text")]

    settings = get_settings()
    with httpx.Client(timeout=120.0) as client:
        dense_vecs = indexers._dense_embed(chunks=chunks, client=client)

    assert(len(dense_vecs) == len(chunks)) # verify same length
    assert(len(i) == settings.semantic_dim for i in dense_vecs)   
    