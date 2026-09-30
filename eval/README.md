# Evaluation

Scores the live engine against the documentation team's gold set
(`docs/docs-proto/starter-kit/alarms/reference-answers.json`).

- **Locally:** `make eval` (needs the stack up and the docs submodule checked out).
  Results, including each code's generated steps, go to `eval/results/retrieval.json`.
- **After a code change:** `make retest` runs unit tests, restarts the
  orchestrator, then `make bench` and `make eval`.
- **CI:** `.github/workflows/eval.yml` is disabled until a self-hosted GPU runner exists.

What each score means, and how far to trust it, is documented at the top of
`run_eval.py`. In short: retrieval scores (hit, precision, recall, MRR) compare
citations with the gold `doc_refs`. Answer scores compare the generated steps with
the gold `resolution_steps`. `fix_present` asks whether the step that actually
resolves the alarm is there, using the key phrases in `fix_terms.json`.

`fix_terms.json` is hand-written from the gold answers. When a gold answer changes
or a code is added, update it too; `tests/test_eval_answer.py` fails if a gold code
has no entry.

Not yet wired: an LLM-judged faithfulness score, and failing the run when a score
regresses below a threshold.
