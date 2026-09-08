"""Ragas / DeepEval harness against the gold set (docs/reference-answers.json).

Runs offline on a GPU runner or locally (`make eval`). Exercises the live
/resolve pipeline and scores retrieval hit-rate + answer faithfulness. This is a
stub wiring the entrypoint; metric wiring is the RAG team's next step.
"""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", default="docs/reference-answers.json")
    args = parser.parse_args()

    gold_path = Path(args.gold)
    if not gold_path.exists():
        raise SystemExit(f"gold set not found: {gold_path} (is the docs submodule checked out?)")

    gold = json.loads(gold_path.read_text())
    print(f"loaded {len(gold)} reference answers from {gold_path}")
    # TODO(rag-team): call /api/v1/resolve per code, score with Ragas/DeepEval,
    # push results to Langfuse, fail the run if below threshold.


if __name__ == "__main__":
    main()
