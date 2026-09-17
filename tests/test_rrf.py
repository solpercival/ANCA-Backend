from rag_engine.retrieval.hybrid import reciprocal_rank_fusion
from rag_engine.retrieval.interfaces import Chunk


def test_rrf_rewards_agreement():
    a = Chunk(chunk_id="x", text="", source="s")
    b = Chunk(chunk_id="y", text="", source="s")
    # x is top of both lists -> must rank first after fusion.
    fused = reciprocal_rank_fusion([[a, b], [a, b]], k=60)
    assert fused[0].chunk_id == "x"


def test_rrf_dedupes():
    a = Chunk(chunk_id="x", text="", source="s")
    fused = reciprocal_rank_fusion([[a], [a]], k=60)
    assert len(fused) == 1
