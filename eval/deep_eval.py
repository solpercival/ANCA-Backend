"""DeepEval + Langfuse scaffolding for the RAG quality gate.

This module intentionally keeps the integration logic deterministic and easy to
run in hosted CI: it validates threshold checks using structured outputs and
optionally emits traces to Langfuse when credentials are configured.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLDS = {
    "faithfulness": 0.85,
    "groundedness": 0.80,
    "relevance": 0.80,
}


def _maybe_langfuse():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        return None

    try:
        from langfuse import Langfuse
    except ImportError:  # pragma: no cover - optional dependency in local dev
        return None

    return Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
    )


def load_result(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path("eval/results/latest.json")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def score_snapshot(result: dict[str, Any]) -> dict[str, float]:
    """Small fallback evaluator for structured LLM outputs.

    This is intentionally deterministic and allows CI to run without a GPU or a
    full model-side evaluator. Replace this with DeepEval metrics once the live
    RAG dataset is wired in.
    """
    citation_count = len(result.get("citation_ids", []))
    step_count = int(result.get("step_count", 0))
    confidence = float(result.get("confidence", 0.0))

    faithfulness = min(1.0, max(0.0, confidence))
    groundedness = 1.0 if citation_count > 0 else 0.0
    relevance = 1.0 if step_count > 0 else 0.0

    return {
        "faithfulness": round(faithfulness, 3),
        "groundedness": round(groundedness, 3),
        "relevance": round(relevance, 3),
    }


def assert_thresholds(scores: dict[str, float], thresholds: dict[str, float] | None = None) -> None:
    thresholds = thresholds or DEFAULT_THRESHOLDS
    failures = {
        name: {"required": value, "actual": scores.get(name, 0.0)}
        for name, value in thresholds.items()
        if scores.get(name, 0.0) < value
    }
    if failures:
        raise SystemExit(f"DeepEval thresholds failed: {json.dumps(failures, indent=2)}")


def log_langfuse_trace(result: dict[str, Any], scores: dict[str, float]) -> None:
    client = _maybe_langfuse()
    if client is None:
        return

    trace = client.trace(name="rag-eval")
    trace.generation(
        name="resolve-snapshot",
        input={"query": result.get("query")},
        output={"status": result.get("status")},
        metadata={**scores, "code": result.get("code", "")},
    )


def run_quality_gate(path: str | Path | None = None) -> dict[str, float]:
    result = load_result(path)
    scores = score_snapshot(result)
    assert_thresholds(scores)
    log_langfuse_trace(result, scores)
    return scores


def main() -> None:
    scores = run_quality_gate()
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
