# Evaluation

Scores the live engine against the documentation team's gold set
(`docs/reference-answers.json`) using Ragas / DeepEval.

- **Locally:** `make eval` (needs the model servers up and the docs submodule checked out).
- **CI:** `.github/workflows/eval.yml` — disabled until a self-hosted GPU runner exists.

Metrics to wire: retrieval hit-rate, context precision, answer faithfulness.
Regressions below threshold should fail the run.
