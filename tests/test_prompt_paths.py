"""The resolve prompt labels context by document path, not by where the docs are
checked out, so moving the docs folder does not change the prompt."""

from rag_engine.orchestrator import Orchestrator
from rag_engine.retrieval.interfaces import Chunk

DOC = "user-guide/troubleshoot/coe-device-errors.md"


def test_context_labels_do_not_depend_on_the_checkout_folder():
    contexts = {
        root: Orchestrator._format_context([Chunk(chunk_id="1", text="t", source=root + DOC)])
        for root in ("docs/working_docs/starter-kit/docs/", "docs/docs-proto/starter-kit/docs/")
    }

    assert len(set(contexts.values())) == 1
    assert contexts["docs/docs-proto/starter-kit/docs/"].startswith(f"({DOC})")
