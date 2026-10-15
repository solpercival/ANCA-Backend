# Handoff: answer-quality work on `/resolve` (2026-10-13)

Working notes for continuing this work on another machine. Delete this file before the branch is merged.

## Where things stand

- Branch: `v3-optimization`, based on `v3-relevance-floor` (`1d4a4a4`).
- `8a5b922`: reranker cutoffs, reranker input length, chunk heading paths, section context, wider reranker input, device-name filter exemption.
- `aebda34`: eval gains `step_precision`, `length_ratio` and `EVAL_RUNS`.
- Unit tests: 503 pass.
- The build at `aebda34` is measured; the baseline is recorded below.

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

### Baseline at `aebda34` (2026-10-13, 3 passes, 11 codes, 0 errors)

| Measure | Mean | Min-max |
|---|---|---|
| `step_precision` | 0.491 | 0.479-0.497 |
| `length_ratio` | 1.855 | 1.83-1.868 |
| `step_recall` | 0.499 | 0.497-0.5 |
| `fix_present` / `fix_solved` | 0.682 / 5 | no spread |
| `actionable` | 0.991 | 0.987-1.0 |
| Citation precision / recall | 0.712 / 0.773 | no spread |
| `hit` / `reciprocal_rank` / `coverage_match` | 0.909 / 0.864 / 0.545 | no spread |

Only `am.nc.0001`, `am.nc.0005` and `am.fb.0002` varied between passes; the other eight answers were identical each time.

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
2. **Prompt, subtraction only (done, kept).** Removed the sentence "Include each check the context gives for diagnosing this alarm, such as what a reported value or state means." from `_build_prompt` in `src/rag_engine/orchestrator.py`, and the matching assertion in `tests/test_resolve_response.py`. Result in the table below.
3. **Unsupported-step rule (awaiting a decision).** Drop a step when fewer than half of its key words appear in the context it was generated from. Offline, on the 73 saved steps, this removed 10 of 45 non-matching steps (the invented ones) and 1 of 28 matching ones. It would bring 73 steps to about 62, so it does not reach the target alone.
4. **Latency.** Find the smallest `rerank_k` that still passes the gold chunks to the reranker (30 was chosen from one alarm); try `RERANK_MAX_LENGTH=1024`; check why generation speed fell from about 45 to about 17 tokens/s within a bench run on the laptop.
5. **Missing half-fixes.** `am.nc.0003`, `am.cfg.0001`, `am.lic.0001`, `am.fb.0002`, `am.fb.0003` and `am.nc.0005` still lack part of the fix. Classify each as "not retrieved" or "retrieved but not used" before choosing a fix.
   Classified on 2026-10-14 with `qwen3:8b` (from the `resolve_candidates` / `resolve_ranked` log lines):
   - `am.cfg.0001`, `am.lic.0001`: solved by `qwen3:8b`.
   - `am.nc.0005`: scoring gap. The answer gives the fix as "only one class 1 preparatory word per block"; `eval/fix_terms.json` accepts only "split", "separate block" or "remove duplicate class 1".
   - `am.fb.0002`: retrieved but not used. "Emergency Error" fills the top of the ranking; the answer omits the manufacturer error data.
   - `am.fb.0003`: "Frame Response Error" is retrieved and ranked first, but the log paths are in the page's "Log Files" section, which was candidate 23 of 30 and cut by the reranker.
   - `am.nc.0003`: the search-hierarchy page is ranked 4th and used in the answer, but not cited, because citations are the first three chunks and all three come from `run-part-programs.md` (hence `hit: False`). The "M-Code Modes" section, which holds the PLC half of the fix, is not among the 40 candidates retrieval returns at all, so a larger `rerank_k` would not help.
6. **Later checklist:** a guideline for ANCA on writing alarm descriptions (ANCA will change descriptions only, not the docs or the alarm structure); feeding the alarm description to the generator as a citable source.

If steps 2 and 3 do not reach the targets, the 4B generator is the limit and the next step is testing a stronger model.

Steps 2 and 3 did not reach the targets, and `qwen3:8b` was tested (results in the table below). The repo default stays the 4B build, because the code is tuned for a 6 GB card and ANCA may use Claude as the generator instead of Ollama (`LLM_PROVIDER=anthropic`); `.env.example` documents `qwen3:8b` for machines with 12 GB or more. Not yet done: an eval run with Claude as the generator.

## What was tried and what it showed

| Change | Result |
|---|---|
| Five extra prompt rules against padding | No effect; dropped |
| Relative rerank cutoff at 0.2 | Small precision gain; kept |
| Reranker input 512 to 2048 tokens | Removes off-topic long tables that scored well only because they were cut off; eval flat; kept |
| Reranker instruction rewording | Mixed on both model sizes; dropped |
| Qwen3-Reranker-4B (4-bit) | Ranked gold chunks higher on 3 of 4 alarms, but 4.1 GB and 7.4 s per call on the laptop; not usable there |
| Heading paths, section context, 30 reranked candidates | `fix_present` 0.636 to 0.682, `fix_solved` 4 to 5; citation precision 0.803 to 0.712, recall 0.864 to 0.773; answers twice the gold length |
| Removing the "Include each check the context gives" prompt sentence (3 passes) | `length_ratio` 1.855 to 1.602 (1.592-1.623); `step_precision` 0.491 to 0.519 (0.513-0.522); `step_recall` 0.499 to 0.482; `fix_present` 0.682 and `fix_solved` 5 unchanged; kept. The precision gain comes almost entirely from `am.nc.0002` (0.57 to 1.0); `am.fb.0003` fell from 0.2 to 0.0 and `am.fb.0001` from 0.33 to 0.2 |
| Unsupported-step filter, `STEP_SUPPORT_MIN=0.5` (3 passes, on top of the row above) | Fired on one alarm only: dropped 3 generic steps from `am.fb.0003` (connection, cabling, interference; the gold notes say cabling advice is not in the doc). `length_ratio` 1.602 to 1.534 (1.524-1.555); `step_precision` 0.519 unchanged; `fix_present` 0.682 and `fix_solved` 5 unchanged. Removes invented steps but does not move precision |
| Generator `qwen3:8b` instead of the 4B instruct build (3 passes, RTX 4070 12 GB, filter on) | `fix_present` 0.682 to 0.773, `fix_solved` 5 to 7 (`am.cfg.0001` and `am.lic.0001` now complete); `coverage_match` 0.545 to 0.818; `length_ratio` 1.534 to 1.321 (1.311-1.326); `step_precision` 0.519 to 0.482 (0.477-0.484), partly a wording artefact (`am.lic.0001` gives both gold fixes but scores 0.33). `think: false` is honoured. Answers took 1.5 to 2.8 s in total (generation 0.9 to 2.1 s, rerank 0.4 to 1.1 s) |
| Generator `granite3.3:8b` (3 passes, same setup) | Worse on every answer measure: `fix_present` 0.394 (0.364-0.455), `fix_solved` 3 to 4, `step_precision` 0.374, `length_ratio` 0.765. It never writes the COVERAGE line (`coverage_match` 0.0) and told `am.lic.0001` to set `opcua.enable` to `true`, the opposite of the fix. 1.6 to 4.0 s per answer; dropped |
| Chunker keeps a short label with its block and drops `---` (3 passes, `qwen3:8b`, after re-ingest) | Retrieval better on every measure, no spread: `hit` 0.909 to 1.0, citation precision 0.712 to 0.727, recall 0.773 to 0.818, reciprocal rank 0.864 to 0.894. `am.nc.0003` now cites the search-hierarchy page, and "M-Code Modes" appears among the candidates for the first time (position 41 of 50). Answer measures within noise: `fix_present` 0.788 (0.773-0.818), `step_precision` 0.487, `length_ratio` 1.389 (1.242-1.462); kept |
| `rerank_k` 30 to 50, so the reranker reads every candidate (3 passes, `qwen3:8b`) | No gain: the reranker's top 8 for `am.nc.0003` is unchanged, so it does not pick "M-Code Modes" even when it sees it. Citation precision 0.727 to 0.712 (`am.fb.0004`), `fix_present` 0.773, rerank time 0.6 to 1.4 s against 0.4 to 1.1 s; reverted to 30 |
| Description-style retrieval query for `am.nc.0003`, passed as `query` on one `/resolve` call (no code change) | The query steers ranking strongly: the search-hierarchy page went from 3rd to the top four places (0.98 to 1.00) and is the only document cited. "M-Code Modes" is still not in the reranker's top 8, and `run-part-programs.md` dropped out, so the answer covers only the search-hierarchy half. Evidence that alarm descriptions are a strong lever, and that a narrow description narrows the answer |
| Hybrid search, `EMBEDDING_SETUP=dual` (3 passes, `qwen3:8b`, after `make sparse` and `make reingest`) | Ran end to end, so the sparse path works. Retrieval scores fell: `hit` 1.0 to 0.909, citation precision 0.727 to 0.682, recall 0.818 to 0.773, reciprocal rank 0.894 to 0.864. Answer measures flat (`fix_present` 0.773, `fix_solved` 7). For `am.nc.0003` it lifted "M-Code Modes" from candidate 41 to 9, but the reranker still left it out of its top 8, and the fused order pushed a search-hierarchy chunk the reranker had scored 0.85 out of the 30 it reads. Left off |
| Qwen3-Reranker-4B in 4-bit on the RTX 4070, next to `qwen3:8b` (3 passes; pass 1 had one timeout while the model downloaded, so passes 2 and 3 are quoted) | Mixed: citation precision 0.727 to 0.788, reciprocal rank 0.894 to 0.909, recall 0.818 to 0.773 (`am.nc.0002` lost a gold document), `fix_present` 0.773 and `fix_solved` 7 unchanged (`am.fb.0002` gained its full fix, `am.cfg.0001` lost half). Rerank time 1.4 to 4.9 s against 0.4 to 1.1 s. Its scores are flatter (0.43 to 0.66 where the 0.6B gave 0.60 to 0.98), so the cutoffs tuned for the 0.6B no longer cut. "M-Code Modes" still not in the top 8 for `am.nc.0003`. Not adopted; the 4-bit loading code and its two dependencies were not kept. On a 24 GB card the 4B fits in fp16 with `RERANK_MODEL` alone |
| Alarm `description` field used as the retrieval query (3 passes, `qwen3:8b`; compared with the run just before it under the same fix terms) | Citation precision 0.727 to 0.833, recall 0.818 to 0.864, reciprocal rank 0.894 to 0.955; `step_precision` 0.479 to 0.637; `length_ratio` 1.462 to 1.262; `fix_present` 0.864 to 0.909, `fix_solved` 8 to 9; no spread across passes. `am.fb.0003` now gives the log-file step. `am.nc.0003` and `am.fb.0002` still lack half a fix. Caveats: the 11 descriptions were written by someone who had read the gold answers, and two fix terms ("additional class 1", "log file") were added to score the new wordings; kept |
| High effort (`EVAL_EFFORT=high`, 3 passes, `qwen3:8b`, descriptions on) | As shipped, with thinking on: every score 0. All 33 requests hit the 250-token output cap while reasoning, so every answer was "not covered". With thinking off: works, but no better than medium: `fix_present` 0.788 (0.773-0.818) against 0.909, `fix_solved` 7 to 8 against 9, `step_precision` 0.59 against 0.637; retrieval scores identical; 1.7 to 2.6 s per answer. Thinking is now off in the high preset |
| Generator `qwen3:14b`, the largest of the family the 12 GB card runs (3 passes, descriptions on, medium effort) | Worse than `qwen3:8b` on fixes: `fix_present` 0.818 against 0.909, `fix_solved` 7 against 9, `step_precision` 0.513 against 0.637; shorter answers (`length_ratio` 1.068); retrieval identical. It did not recover either open half-fix (`am.nc.0003`, `am.fb.0002`) and dropped the second fix on `am.cfg.0001` (restart) and `am.lic.0001` (licence). 2.7 to 7.7 s per answer at 13 to 29 tokens/s with the card at 11.8 of 12.3 GB; not adopted |
| The default generator, `qwen3:4b-instruct-2507-q4_K_M`, on the current build (3 passes, descriptions on, medium effort, RTX 4070) | `fix_present` 0.727 against 0.909 for `qwen3:8b`, `fix_solved` 6 against 9, `step_precision` 0.507 against 0.637, `length_ratio` 1.484 against 1.262, `coverage_match` 0.364 against 0.818; retrieval identical; no spread across passes; 1.3 to 2.8 s per answer, the same as the 8B on this card. This is what a default install gets |
| Prompt/context ladder (2026-10-15; 3 passes per rung, `qwen3:8b`, descriptions on; flags `RESOLVE_PROMPT`, `RESOLVE_EVIDENCE_FIRST`, `RESOLVE_SENTENCE_SELECT`, gaps from `eval/diagnose_gaps.py`) | Baseline `fix_present` 0.894 (0.864-0.909), 25 missed gold steps (16 in the prompt, 9 not). a) `RERANK_TOP_N=4`, `CONTEXT_MAX_CHARS=4000`: 0.909 / 9, `length_ratio` 1.143, 22 gaps; the only rung with no loss; kept as the base. b) short prompt: 0.773 / 7, answers too short (0.595); rejected. c) evidence-first: 0.636 / 5 at 180 tokens (evidence lines used the budget), 0.727 / 6 at 320; drops true steps whose sentence the model did not quote; rejected. d) top-12 sentence selection: 0.864 / 8; the model used what it saw (in-prompt gaps 13 to 5) but selection cut supporting text (not-in-prompt 9 to 17); rejected. e) `qwen3:14b` on the production settings: 0.818 / 7, 5.4 s median. Of the 25 gaps: 10 recovered by a-d, 1 only by the 14B, 14 never (8 with no support in the prompt, 6 with support that no rung got used) |
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
