"""Why gold steps are missing from the answers: in the prompt but not used, or not
in the prompt at all.

For each code, every gold resolution step whose key words are mostly absent from the
generated steps is a gap. The gap is "in prompt, not used" when one passage of the
final prompt's context (a line, or a line with the next one) holds most of the gold
step's key words; otherwise it is "not in prompt". Key words are the eval's
content_stems, so this is the same rough lexical signal as step_recall.

Needs the stack running with RESOLVE_DEBUG_PROMPT=true, so each resolve leaves its
context in Redis (debug:context:<code>), and an eval run that wrote the answers:

    RESOLVE_DEBUG_PROMPT=true in .env, make restart, make eval, then
    python -m eval.diagnose_gaps [--results eval/results/retrieval.json] [--out gaps.json]

The context in Redis is from the last request for each code, so with EVAL_RUNS=3 it
is the third pass's context, judged against the first pass's saved steps.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import redis
from eval.run_eval import GOLD_PATH, content_stems, load_gold

# a gold step counts as given when this share of its key words is in the answer
USED = 0.5
# and as present in the prompt when this share is in one context passage
IN_PROMPT = 0.5


def passages(context: str) -> list[str]:
    """Each non-empty context line, and each line joined with the next one, so a
    step stated across a line break (a table header and its row) still matches."""
    lines = [
        ln.strip()
        for ln in context.splitlines()
        if ln.strip() and not set(ln.strip()) <= set("|-: ")
    ]
    joined = [f"{a} {b}" for a, b in zip(lines, lines[1:], strict=False)]
    return lines + joined


def best_support(stems: set[str], context: str) -> tuple[float, str]:
    """(share of `stems` found, passage) for the context passage holding most of them."""
    best = (0.0, "")
    for passage in passages(context):
        share = len(stems & content_stems(passage)) / len(stems)
        if share > best[0]:
            best = (share, passage)
    return best


def diagnose(results: list[dict], gold: dict, contexts: dict[str, str]) -> dict[str, list[dict]]:
    """Every missed gold step per code, with where its support was found."""
    report: dict[str, list[dict]] = {}
    for result in results:
        code = result["code"]
        answer = set()
        for step in result.get("steps", []):
            answer |= content_stems(step)
        gaps = []
        for gold_step in gold.get(code, {}).get("resolution_steps", []):
            stems = content_stems(gold_step)
            if not stems or len(stems & answer) / len(stems) >= USED:
                continue
            share, passage = best_support(stems, contexts.get(code, ""))
            gaps.append(
                {
                    "gold_step": gold_step,
                    "status": "in_prompt_not_used" if share >= IN_PROMPT else "not_in_prompt",
                    "support_share": round(share, 2),
                    "support": passage[:200],
                }
            )
        report[code] = gaps
    return report


def load_contexts(codes: list[str], url: str) -> dict[str, str]:
    """The last resolve context per code from Redis ("" when none was kept)."""
    client = redis.Redis.from_url(url, decode_responses=True)
    return {code: client.get(f"debug:context:{code}") or "" for code in codes}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="eval/results/retrieval.json")
    parser.add_argument("--gold", default=GOLD_PATH)
    parser.add_argument("--out", help="write the per-code report as JSON here")
    parser.add_argument(
        "--redis", default=os.environ.get("EVAL_REDIS_URL", "redis://localhost:6379/0")
    )
    args = parser.parse_args()

    results = json.loads(Path(args.results).read_text(encoding="utf-8"))["results"]
    contexts = load_contexts([r["code"] for r in results], args.redis)
    missing = [code for code, text in contexts.items() if not text]
    if missing:
        print(f"no context kept for {missing}: is RESOLVE_DEBUG_PROMPT=true?")
    report = diagnose(results, load_gold(args.gold), contexts)

    for code, gaps in report.items():
        for gap in gaps:
            share = gap["support_share"]
            print(f"{code}  {gap['status']:<20} {share:.2f}  {gap['gold_step'][:90]}")
    totals = {}
    for gaps in report.values():
        for gap in gaps:
            totals[gap["status"]] = totals.get(gap["status"], 0) + 1
    print("totals:", totals)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
