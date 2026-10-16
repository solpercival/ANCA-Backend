# Evaluation

Scores the live engine against the documentation team's gold set
(`docs/docs-proto/starter-kit/alarms/reference-answers.json`).

- **Locally:** `make eval` (needs the stack up and the docs submodule checked out).
  Results, including each code's generated steps, go to `eval/results/retrieval.json`.
- **After a code change:** `make retest` runs unit tests, restarts the
  orchestrator, then `make bench` and `make eval`.
- **CI:** `.github/workflows/eval.yml` is disabled until a self-hosted GPU runner exists.

The current scores, what has been tried and the open gaps are in
`docs/answer-quality.md`.

What each score means, and how far to trust it, is documented at the top of
`run_eval.py`. In short: retrieval scores (hit, precision, recall, MRR) compare
citations with the gold `doc_refs`. Answer scores compare the generated steps with
the gold `resolution_steps`. `fix_present` asks whether the step that actually
resolves the alarm is there, using the key phrases in `fix_terms.json`.

`fix_terms.json` is hand-written from the gold answers. When a gold answer changes
or a code is added, update it too; `tests/test_eval_answer.py` fails if a gold code
has no entry.

To fail the run when a score falls below a minimum, set `EVAL_MIN` to comma-separated
`name=value` pairs, for example `EVAL_MIN="fix_present=0.68,hit=0.9" make eval`. The
run exits with status 1 and names each score that missed. Set the minimums below the
min-max range of a repeated run (`EVAL_RUNS=3`), or noise will trip them.

`EVAL_EFFORT=low` or `EVAL_EFFORT=high` scores another effort level; unset, the eval uses the
API default (medium).

Not yet wired: an LLM-judged faithfulness score.
