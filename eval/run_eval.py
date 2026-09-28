"""Structured eval harness for local snapshot + DeepEval quality checks.

This module is intentionally deterministic and testable: it normalizes a result
payload into a small JSON artifact, writes it to `eval/results/latest.json`, and
can compare it against a committed baseline in CI.
"""

from __future__ import annotations

import json
import httpx
from pathlib import Path

GOLD_PATH = "docs/docs-proto/starter-kit/alarms/reference-answers.json"
def load_gold(path=GOLD_PATH):
    """Return gold answers keyed by the alarm code"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["answers"]

def same_doc(cited, gold_path):
    """True if a cited file and a gold path refer to the same document"""
    if not cited or not gold_path:
        return False
    if cited == gold_path:
        return True
    if cited.endswith("/" + gold_path):
        return True
    if gold_path.endswith("/" + cited):
        return True
    return False

def score_code(citations, gold_entry):
    """Score an alarm code's citations against its gold documents"""
    # The files the correct answer comes from 
    gold_paths = []
    for ref in gold_entry["doc_refs"]:
        if ref["path"] not in gold_paths:
            gold_paths.append(ref["path"])

    # For each citation, in order check if it's one of the gold files
    correct = []
    for citation in citations:
        is_correct = False
        for gold_path in gold_paths:
            if same_doc(citation["source"], gold_path):
                is_correct = True
        correct.append(is_correct)

    # Find gold files that got cited at least once
    found = []
    for gold_path in gold_paths:
        for citation in citations:
            if same_doc(citation["source"], gold_path):
                found.append(gold_path)
                break

    # Reciprocal rank = 1 / position of the first correct citation
    if True in correct:
        position = correct.index(True) + 1
        reciprocal_rank = 1 / position
    else:
        reciprocal_rank = 0.0

    # Precision = how many of the citations were correct
    if len(citations) > 0:
        precision = correct.count(True)/len(citations)
    else:
        precision = 0.0

    # Recall = how many of the gold files were found
    recall = len(found)/len(gold_paths)

    # At least one gold ile is found
    hit = len(found) > 0

    return {
        "hit": hit,
        "precision": precision,
        "recall": recall,
        "reciprocal_rank": reciprocal_rank,
    }

API_URL = "http://localhost:8080/api/v2"

def fetch_answer(code, api_url=API_URL, token=None):
    """Ask the API to resolve alarm code and return its JSON response"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = {"code": code, "env": {"versions": {}, "locale": "en-US"}}

    response = httpx.post(
        f"{api_url}/resolve", json=body, headers=headers, timeout=120
    )
    response.raise_for_status()
    return response.json()

def get_token(username, password, api_url=API_URL):
    """Log in and return an access token for the API"""
    response = httpx.post(
        f"{api_url}/auth/token",
        data={"username": username, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]

def run_eval(username, password, api_url=API_URL):
    """Call the API for every gold alarm code and score each answer"""
    gold = load_gold()
    token = get_token(username, password, api_url)

    results = []
    for code, gold_entry in gold.items():
        try:
            answer = fetch_answer(code, api_url=api_url, token=token)
        except httpx.HTTPError as error:
            print(f"{code}: request failed ({error})")
            results.append({"code": code, "error": str(error)})
            continue

        scores = score_code(answer["citations"], gold_entry)
        scores["code"] = code
        results.append(scores)
        print(f"{code}: {scores}")

    return results

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
