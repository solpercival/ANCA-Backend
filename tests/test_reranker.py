"""Tests for the reranker implementations.

Qwen3Reranker's scoring is replaced with fixed fake scores, so the sorting and
truncation can be tested without loading the model.
"""

import types

import pytest

from rag_engine.api.schemas import EffortSettings
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.retrieval.reranker import IdentityReranker, Qwen3Reranker


def _chunks(n: int) -> list[Chunk]:
    return [
        Chunk(chunk_id=str(i), text=f"chunk {i}", source="test.md")
        for i in range(n)
    ]


async def test_identity_truncates_and_preserves_order() -> None:
    """Ten chunks in, first five out and the order is unchanged."""
    result = await IdentityReranker().rerank("any query", _chunks(10), effort=EffortSettings(reranker_n=5))
    assert [c.chunk_id for c in result] == ["0", "1", "2", "3", "4"]


async def test_identity_empty_input_returns_empty() -> None:
    """An empty candidate list comes back empty."""
    assert await IdentityReranker().rerank("any query", [], effort=EffortSettings(reranker_n=5)) == []


async def test_qwen3_orders_by_score_and_truncates() -> None:
    """Chunks come back sorted by score truncated to top_n."""
    reranker = Qwen3Reranker()
    reranker._ensure_loaded = lambda: None  # type: ignore[method-assign]
    reranker._score = lambda query, texts: [  # type: ignore[method-assign]
        float(i) for i in range(len(texts) - 1, -1, -1)
    ]

    result = await reranker.rerank("any query", _chunks(10), effort=EffortSettings(reranker_n=3))

    assert [c.chunk_id for c in result] == ["0", "1", "2"]
    assert result[0].score == 9.0


def _scored_reranker(scores: list[float], min_score: float) -> Qwen3Reranker:
    reranker = Qwen3Reranker(min_score=min_score)
    reranker._ensure_loaded = lambda: None  # type: ignore[method-assign]
    reranker._score = lambda query, texts: scores  # type: ignore[method-assign]
    return reranker


async def test_qwen3_drops_chunks_below_min_score() -> None:
    """Low-relevance chunks are cut even when they fit within top_n."""
    reranker = _scored_reranker([0.9, 0.05, 0.6, 0.1], min_score=0.2)

    result = await reranker.rerank("any query", _chunks(4), effort=EffortSettings(reranker_n=4))

    assert [c.chunk_id for c in result] == ["0", "2"]


async def test_qwen3_keeps_best_chunk_when_all_below_min_score() -> None:
    """The generator always gets at least one chunk to judge coverage from."""
    reranker = _scored_reranker([0.05, 0.1, 0.01], min_score=0.2)

    result = await reranker.rerank("any query", _chunks(3), effort=EffortSettings(reranker_n=3))

    assert [c.chunk_id for c in result] == ["1"]


async def test_qwen3_min_score_zero_disables_cutoff() -> None:
    reranker = _scored_reranker([0.05, 0.1, 0.01], min_score=0.0)

    result = await reranker.rerank("any query", _chunks(3), effort=EffortSettings(reranker_n=3))

    assert len(result) == 3


async def test_qwen3_empty_input_returns_empty() -> None:
    """An empty candidate list comes back empty without loading the model."""
    assert await Qwen3Reranker().rerank("any query", [], effort=EffortSettings(reranker_n=5)) == []


# --- device placement (fake torch/transformers: no model is loaded) -------------

class _Moved:
    """Records .to(device) calls; stands in for a model or a tokenized batch."""

    def __init__(self, log):
        self.log = log

    def to(self, device):
        self.log.append(device)
        return self

    def eval(self):
        return self


def _fake_stack(monkeypatch, cuda: bool):
    import sys
    import types

    calls = {"model_to": [], "inputs_to": [], "dtype": None, "loads": 0}

    torch = types.ModuleType("torch")
    torch.float16, torch.float32 = "fp16", "fp32"
    torch.cuda = types.SimpleNamespace(
        is_available=lambda: cuda, get_device_name=lambda i: "Fake GPU"
    )

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(name, padding_side):
            return types.SimpleNamespace(convert_tokens_to_ids=lambda t: {"yes": 1, "no": 0}[t])

    class AutoModelForCausalLM:
        @staticmethod
        def from_pretrained(name, torch_dtype):
            calls["dtype"] = torch_dtype
            calls["loads"] += 1
            return _Moved(calls["model_to"])

    transformers = types.ModuleType("transformers")
    transformers.AutoTokenizer = AutoTokenizer
    transformers.AutoModelForCausalLM = AutoModelForCausalLM
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    return calls


def test_loads_on_gpu_in_fp16_when_cuda_is_available(monkeypatch, caplog):
    calls = _fake_stack(monkeypatch, cuda=True)
    reranker = Qwen3Reranker(model_name="fake/reranker")

    with caplog.at_level("INFO", logger="rag_engine.reranker"):
        reranker._ensure_loaded()

    assert reranker._device == "cuda"
    assert calls["dtype"] == "fp16"
    assert calls["model_to"] == ["cuda"]
    assert "device=cuda gpu=Fake GPU" in caplog.text


def test_falls_back_to_cpu_fp32_and_warns(monkeypatch, caplog):
    calls = _fake_stack(monkeypatch, cuda=False)
    reranker = Qwen3Reranker(model_name="fake/reranker")

    with caplog.at_level("WARNING", logger="rag_engine.reranker"):
        reranker._ensure_loaded()

    assert reranker._device == "cpu"
    assert calls["dtype"] == "fp32"
    assert calls["model_to"] == ["cpu"]
    assert "device=cpu" in caplog.text and "CUDA not visible" in caplog.text


def test_concurrent_first_calls_load_the_model_once(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    calls = _fake_stack(monkeypatch, cuda=True)
    reranker = Qwen3Reranker(model_name="fake/reranker")

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: reranker._ensure_loaded(), range(8)))

    assert calls["loads"] == 1


def test_score_moves_inputs_to_the_model_device(monkeypatch):
    torch = pytest.importorskip("torch")
    monkeypatch.setattr(torch.cuda, "reset_peak_memory_stats", lambda: None)
    inputs_to: list[str] = []

    class Batch(dict):  # a tokenizer's BatchEncoding is a mapping with .to()
        def to(self, device):
            inputs_to.append(device)
            return self

    reranker = Qwen3Reranker(model_name="fake/reranker")
    reranker._device = "cuda"
    reranker._tokenizer = lambda *a, **k: Batch(input_ids=torch.tensor([[1]]))

    class Stop(Exception):
        pass

    def decoder(**kwargs):
        raise Stop  # only the device move before the forward pass matters here

    reranker._model = types.SimpleNamespace(get_decoder=lambda: decoder)
    with pytest.raises(Stop):
        reranker._score("q", ["t"])

    assert inputs_to == ["cuda"]


@pytest.mark.parametrize(("n", "batch", "expected_batches"), [(20, 5, [5, 5, 5, 5]), (7, 5, [5, 2]), (3, 8, [3])])
def test_score_runs_in_batches_and_keeps_order(n, batch, expected_batches):
    torch = pytest.importorskip("torch")
    seen: list[int] = []

    class Batch(dict):
        def to(self, device):
            return self

    def tokenizer(prompts, **kwargs):
        seen.append(len(prompts))
        # encode each pair's index so the fake model can give it a distinct score
        ids = [[int(p.rsplit("doc-", 1)[1].split("<")[0])] for p in prompts]
        return Batch(input_ids=torch.tensor(ids))

    reranker = Qwen3Reranker(model_name="fake/reranker", batch_size=batch)
    reranker._tokenizer = tokenizer
    # "yes" logit rises with the pair index, "no" stays 0
    reranker._yes_no_logits = lambda inputs: torch.stack(
        [torch.zeros(len(inputs["input_ids"])), inputs["input_ids"][:, 0].float()], dim=1
    )

    scores = reranker._score("q", [f"doc-{i}" for i in range(n)])

    assert seen == expected_batches
    assert len(scores) == n
    assert scores == sorted(scores)  # order preserved across batch boundaries


def test_batch_size_defaults_from_settings(monkeypatch):
    from rag_engine.config import get_settings

    monkeypatch.setenv("RERANK_BATCH_SIZE", "4")
    get_settings.cache_clear()
    try:
        assert Qwen3Reranker(model_name="fake/reranker")._batch_size == 4
        assert Qwen3Reranker(model_name="fake/reranker", batch_size=2)._batch_size == 2
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("bias", [False, True])
def test_yes_no_logits_match_full_vocabulary_logits(bias):
    # the two-row shortcut must equal reading "no"/"yes" out of the full LM-head
    # output at the last position -- same scores, without the [batch, seq, vocab] tensor
    torch = pytest.importorskip("torch")
    torch.manual_seed(0)
    batch, seq, hidden_size, vocab = 3, 7, 16, 50
    hidden = torch.randn(batch, seq, hidden_size)
    head = torch.nn.Linear(hidden_size, vocab, bias=bias)

    class Decoder:
        def __call__(self, **inputs):
            return types.SimpleNamespace(last_hidden_state=hidden)

    model = types.SimpleNamespace(get_decoder=Decoder, get_output_embeddings=lambda: head)
    reranker = Qwen3Reranker(model_name="fake/reranker")
    reranker._model, reranker._no_id, reranker._yes_id = model, 11, 42

    with torch.no_grad():
        pair = reranker._yes_no_logits({"input_ids": None})
        full = head(hidden)[:, -1, :]

    expected = torch.stack([full[:, 11], full[:, 42]], dim=1)
    assert pair.shape == (batch, 2)
    assert torch.allclose(pair, expected, atol=1e-5)