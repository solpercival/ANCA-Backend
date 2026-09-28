"""Reranker implementation.

IdentityReranker returns candidates unchanged and serves as the baseline.
Qwen3Reranker scores each query/chunk pair with a cross-encoder.
"""
from __future__ import annotations

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

    def __init__(self, model_name: str | None = None, max_length: int = 4096):
        self._model_name = model_name or get_settings().rerank_model
        self._max_length = max_length
        self._model: Any = None
        self._tokenizer: Any = None
        self._yes_id: int = -1
        self._no_id: int = -1

    def _ensure_loaded(self) -> None:
        # Import is intentionally kept here, inside the backend implementation.
        if self._model is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_name, padding_side="left"
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_name,
            torch_dtype=torch.float16,
            device_map="auto",
        ).eval()
        self._yes_id = self._tokenizer.convert_tokens_to_ids("yes")
        self._no_id = self._tokenizer.convert_tokens_to_ids("no")

    def _score(self, query: str, texts: list[str]) -> list[float]:
        import torch

        prompts = [
            PREFIX
            + f"<Instruct>: {INSTRUCTION}\n<Query>: {query}\n<Document>: {text}"
            + SUFFIX
            for text in texts
        ]
        inputs = self._tokenizer(
            prompts,
            padding=True,
            truncation=True,
            max_length=self._max_length,
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = self._model(**inputs).logits[:, -1, :]
        pair = torch.stack([logits[:, self._no_id], logits[:, self._yes_id]], dim=1)
        return torch.softmax(pair, dim=1)[:, 1].tolist()

    async def rerank(
        self, query: str, chunks: list[Chunk], top_n: int
    ) -> list[Chunk]:
        """Score each chunk against the query and return the top_n by relevance."""
        if not chunks:
            return []
        self._ensure_loaded()
        scores = self._score(query, [c.text for c in chunks])
        for chunk, score in zip(chunks, scores, strict=True):
            chunk.score = score
        return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_n]
