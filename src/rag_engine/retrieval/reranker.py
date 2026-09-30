"""Reranker implementation.

IdentityReranker returns candidates unchanged and serves as the baseline.
Qwen3Reranker scores each query/chunk pair with a cross-encoder.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any

from rag_engine.config import get_settings
from rag_engine.retrieval.interfaces import Chunk

PREFIX = (
    '<|im_start|>system\nJudge whether the Document meets the requirements '
    'based on the Query and the Instruct provided. Note that the answer can '
    'only be "yes" or "no".<|im_end|>\n<|im_start|>user\n'
)
SUFFIX = '<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
INSTRUCTION = "Given a CNC documentation query, judge whether the document answers it"

log = logging.getLogger("rag_engine.reranker")


class IdentityReranker:
    """No-op reranker: preserves incoming order, truncates to top_n."""

    async def rerank(
        self, query: str, chunks: list[Chunk], top_n: int
    ) -> list[Chunk]:
        """Return the first top_n chunks unchanged."""
        del query  # unused: ordering is left to the caller
        return list(chunks[:top_n])


class Qwen3Reranker:
    """Cross-encoder reranker backed by Qwen3-Reranker.

    Model and tokenizer load lazily on first use so that importing this module
    stays free of heavy dependencies and CI can run without models.
    """

    def __init__(
        self,
        model_name: str | None = None,
        max_length: int = 4096,
        batch_size: int | None = None,
        min_score: float | None = None,
    ):
        self._model_name = model_name or get_settings().rerank_model
        self._max_length = max_length
        self._batch_size = max(1, batch_size or get_settings().rerank_batch_size)
        self._min_score = get_settings().rerank_min_score if min_score is None else min_score
        self._model: Any = None
        self._tokenizer: Any = None
        self._yes_id: int = -1
        self._no_id: int = -1
        self._device: str = "cpu"  # set to "cuda" by _load when available
        self._load_lock = threading.Lock()

    def _ensure_loaded(self) -> None:
        # Import is intentionally kept here, inside the backend implementation.
        if self._model is not None:
            return
        with self._load_lock:  # concurrent first requests must not load it twice
            if self._model is None:
                self._load()

    def _load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        # fp16 halves VRAM on GPU; CPU kernels need fp32
        dtype = torch.float16 if self._device == "cuda" else torch.float32

        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_name, padding_side="left"
        )
        self._model = (
            AutoModelForCausalLM.from_pretrained(self._model_name, torch_dtype=dtype)
            .to(self._device)
            .eval()
        )
        self._yes_id = self._tokenizer.convert_tokens_to_ids("yes")
        self._no_id = self._tokenizer.convert_tokens_to_ids("no")
        if self._device == "cpu":
            # not fatal, but far slower than GPU and easy to miss: say so loudly
            log.warning(
                "reranker_loaded model=%s device=cpu -- CUDA not visible to this "
                "process; reranking will be slow",
                self._model_name,
            )
        else:
            log.info(
                "reranker_loaded model=%s device=cuda gpu=%s dtype=fp16",
                self._model_name, torch.cuda.get_device_name(0),
            )

    def _score(self, query: str, texts: list[str]) -> list[float]:
        import torch

        prompts = [
            PREFIX
            + f"<Instruct>: {INSTRUCTION}\n<Query>: {query}\n<Document>: {text}"
            + SUFFIX
            for text in texts
        ]
        t0 = time.perf_counter()
        if self._device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        # Small batches bound the activation memory: all 20 pairs x 512 tokens at once
        # peaked at ~1.3 GB over the weights, enough to push Ollama off a 6 GB card.
        # Each batch is scored independently, so the scores are unchanged.
        scores: list[float] = []
        max_seq = 0
        for start in range(0, len(prompts), self._batch_size):
            inputs = self._tokenizer(
                prompts[start:start + self._batch_size],
                padding=True,
                truncation=True,
                max_length=self._max_length,
                return_tensors="pt",
            ).to(self._device)
            max_seq = max(max_seq, inputs["input_ids"].shape[1])
            with torch.no_grad():
                pair = self._yes_no_logits(inputs)
            scores.extend(torch.softmax(pair.float(), dim=1)[:, 1].tolist())  # syncs the GPU
        if self._device == "cuda":
            log.info(
                "rerank_forward pairs=%d batch=%d seq_len=%d secs=%.3f torch_peak_mib=%d torch_reserved_mib=%d",
                len(texts), self._batch_size, max_seq, time.perf_counter() - t0,
                torch.cuda.max_memory_allocated() // 2**20, torch.cuda.memory_reserved() // 2**20,
            )
        return scores

    def _yes_no_logits(self, inputs: Any) -> Any:
        """[batch, 2] logits for ("no", "yes") at each pair's final token.

        Only those two vocabulary entries are ever read, so the LM head is applied
        to the last position and to those two rows alone. The full-vocabulary
        logits over every position ([batch, seq, ~152k] -- about 3 GB in fp16 for
        20 pairs x 512 tokens) are never materialised; that tensor, not the model,
        was what crowded Ollama off the GPU. Padding is on the left, so position
        -1 is every pair's real last token.
        """
        import torch

        hidden = self._model.get_decoder()(**inputs).last_hidden_state[:, -1, :]
        head = self._model.get_output_embeddings()
        rows = torch.tensor([self._no_id, self._yes_id], device=hidden.device)
        pair = hidden @ head.weight[rows].T
        if getattr(head, "bias", None) is not None:
            pair = pair + head.bias[rows]
        return pair

    async def rerank(
        self, query: str, chunks: list[Chunk], top_n: int
    ) -> list[Chunk]:
        """Score each chunk against the query and return the top_n by relevance."""
        if not chunks:
            return []
        # model load (first call) and the forward pass are blocking; keep them off
        # the event loop so other requests and /ready stay responsive
        await asyncio.to_thread(self._ensure_loaded)
        scores = await asyncio.to_thread(self._score, query, [c.text for c in chunks])
        for chunk, score in zip(chunks, scores, strict=True):
            chunk.score = score
        ranked = sorted(chunks, key=lambda c: c.score, reverse=True)[:top_n]
        # Scores are P("yes, this document answers the query"). Off-topic chunks that
        # still make the top_n reach the prompt and get used (e.g. a firmware-upgrade
        # page cited for an EtherCAT state alarm), so drop them -- but always keep the
        # best one, so the generator can still decide coverage itself.
        kept = [c for c in ranked if c.score >= self._min_score] or ranked[:1]
        log.info(
            "rerank_cutoff min_score=%.2f kept=%d/%d scores=%s",
            self._min_score, len(kept), len(ranked), [round(c.score, 2) for c in ranked],
        )
        return kept
