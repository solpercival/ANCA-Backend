"""Eval harness for the resolve API.

Two modes:
- `python -m eval.run_eval --gold <file>`: live eval. Logs in, calls /resolve
  for every alarm code in the gold set, scores the cited documents against the
  gold doc_refs (hit rate, precision, recall, MRR) and the generated steps
  against the gold resolution_steps (step_recall, actionable, coverage_match,
  and fix_present: is the resolving action from eval/fix_terms.json there),
  and writes eval/results/retrieval.json. Needs the stack running and
  EVAL_USERNAME / EVAL_PASSWORD set.
- `python eval/run_eval.py`: the offline snapshot check used by the rag-eval
  and rag-snapshot CI workflows. Writes eval/results/latest.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import httpx

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

# Words that carry no meaning on their own, ignored when comparing steps
STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "are", "was", "has", "have",
    "its", "it's", "into", "any", "all", "not", "but", "can", "may", "will", "then",
    "your", "you", "per", "via", "each", "same", "one", "only", "again", "if",
}

# Verbs a resolution step should start with ("Restart the system", "Check ...")
ACTION_VERBS = {
    "check", "verify", "confirm", "ensure", "set", "reset", "restart", "reboot",
    "reinitialise", "reinitialize", "power-cycle", "power", "replace", "inspect",
    "record", "note", "review", "clear", "acknowledge", "enable", "disable", "update",
    "upgrade", "reduce", "increase", "add", "remove", "correct", "fix", "assign",
    "map", "change", "adjust", "configure", "reconfigure", "install", "reinstall",
    "purchase", "contact", "compare", "measure", "test", "use", "create", "rename",
    "move", "edit", "open", "run", "reload", "retry", "wait", "reseat", "tighten",
    "reconnect", "connect", "disconnect", "locate", "find", "look", "make", "define",
    "provide", "specify", "program", "activate", "deactivate",
    # kept in step with the engine's _ACTION_VERBS so the two agree on what a step is
    "acknowledge", "attach", "detach", "release", "split", "upload", "transfer",
    "re-initialise", "re-initialize", "re-run", "rerun", "recover", "place", "insert",
    "reinitialise", "reinitialize", "synchronise", "synchronize", "coordinate",
    "identify", "determine", "interpret", "investigate", "consult", "refer", "read",
    "select", "switch", "turn", "apply", "save", "load", "start", "stop", "restore",
}

def content_stems(text):
    """Meaningful words of a sentence, cut to 5 letters so that
    'restart'/'restarting' or 'reinitialise'/'reinitialising' still match"""
    words = [w.strip("._-") for w in re.findall(r"[a-z0-9][a-z0-9_.\-]*", text.lower())]
    return {w[:5] for w in words if len(w) >= 3 and w not in STOPWORDS}

def score_answer(answer, gold_entry):
    """Score the generated steps against the gold resolution steps

    step_recall: for each gold step, the share of its key words found anywhere
        in the generated steps, averaged over the gold steps
    actionable: share of generated steps that start with an action verb
        (a step that just restates the alarm fails this)
    coverage_match: 1 if our doc_coverage equals the gold doc_coverage
    """
    steps = answer.get("steps", [])
    answer_stems = set()
    for step in steps:
        answer_stems |= content_stems(step)

    recalls = []
    for gold_step in gold_entry.get("resolution_steps", []):
        gold_stems = content_stems(gold_step)
        if gold_stems:
            recalls.append(len(gold_stems & answer_stems) / len(gold_stems))
    step_recall = sum(recalls) / len(recalls) if recalls else 0.0

    action_steps = 0
    for step in steps:
        words = step.split()
        if words and words[0].lower().strip(".,:;") in ACTION_VERBS:
            action_steps += 1
    actionable = action_steps / len(steps) if steps else 0.0

    coverage_match = answer.get("doc_coverage") == gold_entry.get("doc_coverage")

    return {
        "step_recall": step_recall,
        "actionable": actionable,
        "coverage_match": float(coverage_match),
    }

FIX_TERMS_PATH = Path(__file__).parent / "fix_terms.json"

def load_fix_terms(path=FIX_TERMS_PATH):
    """Return the key-fix phrase groups keyed by alarm code"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {code: groups for code, groups in data.items() if not code.startswith("_")}

def score_fix(steps, groups):
    """Share of the key fixes (e.g. 'restart', 'set opcua.enable false') that
    appear in the steps. A group is met when any of its phrases appears."""
    text = " ".join(steps).lower()
    met = 0
    for phrases in groups:
        if any(phrase in text for phrase in phrases):
            met += 1
    return met / len(groups)

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

def run_eval(username, password, api_url=API_URL, gold_path=GOLD_PATH):
    """Call the API for every gold alarm code and score each answer."""
    gold = load_gold(gold_path)
    fix_terms = load_fix_terms()
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
        scores.update(score_answer(answer, gold_entry))
        if code in fix_terms:
            scores["fix_present"] = score_fix(answer.get("steps", []), fix_terms[code])
        scores["code"] = code
        results.append(scores)
        print(f"{code}: {scores}")
        # saved to the results file (not printed) so answers can be inspected later
        scores["steps"] = answer.get("steps", [])
        scores["doc_coverage"] = answer.get("doc_coverage")

    return results

def summarize(results):
    """Average each score across all alarm codes. Failed calls count as zero"""
    totals = {
        "hit": 0, "precision": 0, "recall": 0, "reciprocal_rank": 0,
        "step_recall": 0, "actionable": 0, "coverage_match": 0,
    }
    errors = 0

    for result in results:
        if "error" in result:
            errors += 1
            continue
        for name in totals:
            totals[name] += result[name]

    summary = {}
    for name in totals:
        summary[name] = round(totals[name]/len(results), 3)

    # fix_present only exists for codes listed in fix_terms.json
    fix_scores = [r["fix_present"] for r in results if "fix_present" in r]
    if fix_scores:
        summary["fix_present"] = round(sum(fix_scores)/len(fix_scores), 3)
        summary["fix_solved"] = sum(1 for s in fix_scores if s == 1.0)
    summary["codes"] = len(results)
    summary["errors"] = errors
    return summary

def run_live_eval(gold_path):
    """Run the real eval against the API and save the scores"""
    username = os.environ["EVAL_USERNAME"]
    password = os.environ["EVAL_PASSWORD"]
    api_url = os.environ.get("EVAL_API_URL", API_URL)

    results = run_eval(username, password, api_url, gold_path)
    summary = summarize(results)

    output_path = Path("eval/results/retrieval.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"summary": summary, "results": results}, indent=2),
        encoding="utf-8",
    )
    print(summary)
    print(f"wrote {output_path}")

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", help="gold answers file; runs the live eval against the API")
    args = parser.parse_args()

    if args.gold:
        run_live_eval(args.gold)
        return

    # When there is no --gold. Snapshot check used by the rag-eval and rag-snapshot CI workflows
    out = run_local_eval()
    output_path = Path("eval/results/latest.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
