"""Structured eval harness for local snapshot + DeepEval quality checks.

This module is intentionally deterministic and testable: it normalizes a result
payload into a small JSON artifact, writes it to `eval/results/latest.json`, and
can compare it against a committed baseline in CI.
"""

from __future__ import annotations

import json
from pathlib import Path

GOLD_PATH = "docs/docs-proto/starter-kit/alarms/reference-answers.json"
def load_gold(path=GOLD_PATH):
    """Return gold answers keyed by the alarm code"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["answers"]

def normalize_result(payload: dict) -> dict:
    """Convert a raw model result into a stable normalized artifact.

    We intentionally compare structured fields instead of raw prose, because LLM
    wording may vary while the fix remains correct.
    """
    return {
        "query": payload.get("query", ""),
        "code": payload.get("code", ""),
        "citation_ids": [c["chunk_id"] for c in payload.get("citations", [])],
        "step_count": len(payload.get("steps", [])),
        "confidence": round(float(payload.get("confidence", 0.0)), 3),
        "status": payload.get("status", "ok"),
    }


def compare_snapshot(generated_path: Path | str, expected_path: Path | str) -> None:
    generated = json.loads(Path(generated_path).read_text(encoding="utf-8"))
    expected = json.loads(Path(expected_path).read_text(encoding="utf-8"))

    if generated != expected:
        raise SystemExit(
            "Snapshot mismatch\n"
            f"Generated: {json.dumps(generated, indent=2)}\n"
            f"Expected: {json.dumps(expected, indent=2)}"
        )


def run_local_eval() -> dict:
    """Placeholder to be replaced by the real app call and metric collection."""
    result = {
        "query": "motor stalls after startup",
        "code": "am.fb.0002",
        "steps": [
            "Check the drive and power supply",
            "Inspect the motor wiring",
            "Verify the control board status",
        ],
        "citations": [
            {"source": "manual.md", "chunk_id": "c1"},
            {"source": "faq.md", "chunk_id": "c9"},
        ],
        "confidence": 0.891234,
        "status": "ok",
    }
    return normalize_result(result)


def main() -> None:
    out = run_local_eval()
    output_path = Path("eval/results/latest.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
