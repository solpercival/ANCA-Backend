# Handoff: answer-quality work on `/resolve` (2026-10-13)

Working notes for continuing this work on another machine. Delete this file before the branch is merged.

## Where things stand

- Branch: `v3-optimization`, based on `v3-relevance-floor` (`1d4a4a4`).
- `8a5b922`: reranker cutoffs, reranker input length, chunk heading paths, section context, wider reranker input, device-name filter exemption.
- `aebda34`: eval gains `step_precision`, `length_ratio` and `EVAL_RUNS`.
- Unit tests: 503 pass.
- Not yet measured: the build at `aebda34`. The baseline run below is the next step.

## Setting up on a new machine

1. `git fetch && git switch v3-optimization`, then `git submodule update --init` for the docs.
2. `cp .env.example .env` and fill in the secrets. The reranker values this work relies on are already in `.env.example`: `RERANK_MIN_SCORE=0.02`, `RERANK_RELATIVE_MIN=0.2`, `RERANK_MIN_KEEP=2`, `RERANK_MAX_LENGTH=2048`.
3. Create the virtual environment on the Linux filesystem, not on a Windows drive under WSL (imports from a Windows drive made `make test` take over 2 minutes; the tests themselves run in about 14 seconds):
   ```bash
   python3.12 -m venv ~/.venvs/anca-backend
   ~/.venvs/anca-backend/bin/pip install -e ".[dev]"
   ln -s ~/.venvs/anca-backend .venv
   ```
4. `make up`, then `make ingest`. The database is local to each machine, and this branch changes how documents are chunked, so every document is embedded again (about 4,500 chunks).
5. Always start the stack through `make`. A plain `docker compose up` drops the GPU reservation and everything silently runs on CPU.

## Next step: the baseline run

```bash
make restart
EVAL_RUNS=3 make eval
```

Record the summary line and the `min-max over 3 passes` line. Every later change is compared with this run, and a difference smaller than the min-max range is noise. Numbers from the old machine (6 GB laptop GPU) are not comparable for latency.

## Targets

| Measure | Last measured | Target |
|---|---|---|
| Steps vs gold (`length_ratio`) | 1.97 (73 steps vs 37) | 1.3 or lower |
| `step_precision` | 0.38 | 0.60 or higher |
| `fix_present` / `fix_solved` | 0.682 / 5 | not lower |
| Invented steps about alarm values | 2 | 0 |
| Typical answer time | 5 to 12 s | about 6 s |

## Remaining plan

1. **Baseline** (above).
2. **Prompt, subtraction only.** Remove the sentence "Include each check the context gives for diagnosing this alarm, such as what a reported value or state means." from `_build_prompt` in `src/rag_engine/orchestrator.py`, and the matching assertion in `tests/test_resolve_response.py`. Keep it only if `step_precision` rises and `fix_present` does not fall beyond the noise range.
3. **Unsupported-step rule (awaiting a decision).** Drop a step when fewer than half of its key words appear in the context it was generated from. Offline, on the 73 saved steps, this removed 10 of 45 non-matching steps (the invented ones) and 1 of 28 matching ones. It would bring 73 steps to about 62, so it does not reach the target alone.
4. **Latency.** Find the smallest `rerank_k` that still passes the gold chunks to the reranker (30 was chosen from one alarm); try `RERANK_MAX_LENGTH=1024`; check why generation speed fell from about 45 to about 17 tokens/s within a bench run on the laptop.
5. **Missing half-fixes.** `am.nc.0003`, `am.cfg.0001`, `am.lic.0001`, `am.fb.0002`, `am.fb.0003` and `am.nc.0005` still lack part of the fix. Classify each as "not retrieved" or "retrieved but not used" before choosing a fix.
6. **Later checklist:** a guideline for ANCA on writing alarm descriptions (ANCA will change descriptions only, not the docs or the alarm structure); feeding the alarm description to the generator as a citable source.

If steps 2 and 3 do not reach the targets, the 4B generator is the limit and the next step is testing a stronger model.

## What was tried and what it showed

| Change | Result |
|---|---|
| Five extra prompt rules against padding | No effect; dropped |
| Relative rerank cutoff at 0.2 | Small precision gain; kept |
| Reranker input 512 to 2048 tokens | Removes off-topic long tables that scored well only because they were cut off; eval flat; kept |
| Reranker instruction rewording | Mixed on both model sizes; dropped |
| Qwen3-Reranker-4B (4-bit) | Ranked gold chunks higher on 3 of 4 alarms, but 4.1 GB and 7.4 s per call on the laptop; not usable there |
| Heading paths, section context, 30 reranked candidates | `fix_present` 0.636 to 0.682, `fix_solved` 4 to 5; citation precision 0.803 to 0.712, recall 0.864 to 0.773; answers twice the gold length |
| Extra model call that selects which steps to keep | Failed offline: lost the fix on two alarms in each of two prompt variants; not built |

Other findings worth keeping:

- `step_recall` rewards longer answers. Read `step_precision` and `fix_present` first.
- Off-topic sections reach the generator with high reranker scores (`am.fb.0002` gets "Frame Response Error" at 0.96; `am.fb.0001` gets "Diagnostics" at 0.87). The 0.6B reranker cannot separate them, and they are where tangential steps come from.
- Four of 18 answers hit the 180-token output limit, which also cuts off their CAUSE lines.
- Loosening the duplicate-step filter is not safe: at a 0.7 threshold it also drops distinct actions ("Detach the axis" / "Attach the axis").

## On a machine with more GPU memory

The 4B reranker needed about 4.1 GB at peak in 4-bit form, next to roughly 3 GB for the generator and embedding models. On a card with 12 GB it should fit, and it was the one change that visibly improved ranking, so it is worth re-testing there (`RERANK_MODEL=Qwen/Qwen3-Reranker-4B`; loading it in 4-bit needs `bitsandbytes` and `accelerate`, which are not in the image). A larger generator may also fit. Neither has been tried on that hardware.

## Working rules for this project

- All of this work stays on `v3-optimization`, one commit per change; commit messages are written for teammates; no AI attribution lines in commits.
- Never commit `eval/results/retrieval.json`; leave `docs/working_docs` alone; do not reformat unrelated code.
- No numeric cap on the number of steps.
- Keep new tests to the one or two that pin a behaviour; run touched test files while iterating and the full suite once before a commit.
- Long stack commands (`make ingest`, `make restart`, `make bench`, `make eval`) are run by the developer, who pastes the results back.
