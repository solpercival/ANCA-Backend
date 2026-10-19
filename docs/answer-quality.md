# Answer quality of `/resolve`: state, findings and next steps

This is for whoever maintains the engine next. It covers:

- how good the `/resolve` answers are and how that was measured;
- what was tried, and why each change was kept or dropped;
- what is still open.

The raw eval output for the 15-16 Oct 2026 tuning runs is in
`eval/results/ladder/` (see its README).

## Current state (16 Oct 2026)

The settings are the defaults in `src/rag_engine/config.py` and `.env.example`:

| Setting | Value |
|---|---|
| Generator | `qwen3:8b` via Ollama, temperature 0, `think: false`, 180 output tokens |
| Retrieval | dense embeddings only (`EMBEDDING_SETUP=unified`), 50 candidates |
| Reranker | `Qwen/Qwen3-Reranker-0.6B` on the first 30 candidates; it keeps 8 (`RERANK_TOP_N=8`) |
| Context | up to 8000 characters (`CONTEXT_MAX_CHARS`) |
| Retrieval query | the alarm's title and `description` |
| Step filter | a step is dropped when under 50% of its key words are in the context (`STEP_SUPPORT_MIN=0.5`) |

On the gold set (11 alarms, `make eval` after a clean `make reingest`, RTX 4070 12 GB):

| Measure | Score |
|---|---|
| `fix_present` / `fix_solved` | 0.909 / 9 of 11 |
| `step_precision` | 0.637 |
| `length_ratio` (answer steps / gold steps) | 1.262 |
| Citation precision / recall / reciprocal rank | 0.833 / 0.864 / 0.955 |
| Time per answer | about 1.3 to 2.8 s (first request after a start: about 17 s, while the models load) |

10 runs in a row, including after restarts, all gave these numbers. At temperature
0, the same alarm with the same retrieved text gets the same answer.

On a GPU with under about 6 GB free, use `LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M`.
It scored 0.727 / 6 at about the same speed on the RTX 4070.

## How to measure a change

1. `make reingest`, whenever the chunker, the embedding setup or the documents
   changed. **Also before any comparison run.** An index left from an earlier
   build retrieved the same documents with different chunk text, and moved
   `fix_solved` between 8 and 9 for no visible reason (see
   `eval/results/ladder/README.md`).
2. `make restart`, then `EVAL_RUNS=3 make eval`. The summary line and the
   `min-max over 3 passes` line are the result. A difference smaller than the
   min-max range is noise.
3. Read `fix_present` and `step_precision` first. `step_recall` rewards longer
   answers.
4. Check each alarm, not just the totals. A total can stay the same while one alarm
   gains and another loses: that hid the cost of `STEP_SUPPORT_MIN=0.6` (below).
5. To see why a gold step is missing, set `RESOLVE_DEBUG_PROMPT=true`, run the eval,
   then `.venv/bin/python -m eval.diagnose_gaps`. For
   each missed gold step it says whether its supporting text was in the prompt
   (`in_prompt_not_used`, a generation gap) or not (`not_in_prompt`, a retrieval gap).

The gold set is small. One alarm is worth 0.045 of `fix_present`, so adding gold
answers improves every later comparison more than any single tuning change can.

## Open gaps

| Alarm | What is missing | Why |
|---|---|---|
| `am.fb.0002` | "Interpret the manufacturer-specific error data using the drive manufacturer's manual" | The text is in the prompt, but inside a table, and the model does not turn table rows into steps. A prompt rule asking it to use table contents lost a fix elsewhere (see below) |
| `am.nc.0003` | "Decide whether M101 belongs in the PLC or as an EPPL part program" | The "M-Code Modes" section that holds it is not retrieved. Hybrid search lifted it from candidate 41 to 9, but the reranker still did not keep it |

Smaller open points:

- `src/rag_engine/api/schemas.py`: the alarm-code pattern
  (`^[a-z]{2,4}\.[a-z]{2,6}\.\d{4}$`) is inferred from the starter-kit examples and
  still needs confirming with the documentation team.
- mypy reports 21 errors, and CI runs it as advisory only:
  - `stores/search.py`: list element types;
  - `providers.py`: request payload dict types;
  - `orchestrator.py`: `ResolveResponse` fields with defaults reported as missing, and
    a tuple return type;
  - one each in `auth/session_store.py`, `auth/service.py` and `retrieval/reranker.py`.

  None is known to fail at run time. The one that did, `Langfuse.trace` under SDK 3+,
  is fixed by pinning `langfuse<3`.
- `.github/workflows/eval.yml` is disabled until a self-hosted GPU runner exists.

## What was tried

The measurements are 3 passes each with `qwen3:8b`, unless the row says otherwise.
The rows are in the order the changes were tried, so earlier rows ran on an older
build.

| Change | Result | Decision |
|---|---|---|
| Reranker cutoffs: relative cutoff 0.2, floor 0.02, keep at least 2 | Small precision gain | Kept |
| Reranker input 512 to 2048 tokens | Long off-topic tables no longer score well just because they were cut off | Kept |
| Heading paths, section context, 30 reranked candidates | `fix_present` 0.636 to 0.682 | Kept |
| Removing the prompt sentence "Include each check the context gives…" | `length_ratio` 1.855 to 1.602, precision 0.491 to 0.519, fixes unchanged | Kept |
| Unsupported-step filter at 0.5 | Drops invented generic steps (cabling, interference) | Kept |
| `qwen3:8b` instead of the 4B instruct build | `fix_present` 0.682 to 0.773, `coverage_match` 0.545 to 0.818, same speed | Kept, now the default |
| Chunker keeps a short label with its block | Retrieval better on every measure (`hit` 0.909 to 1.0) | Kept |
| Alarm `description` as the retrieval query | Citation precision 0.727 to 0.833, `step_precision` 0.479 to 0.637, `fix_present` 0.864 to 0.909 | Kept. The 11 descriptions were written by someone who had read the gold answers, so this may be optimistic for new alarms. See `docs/alarm-description-guidelines.md` |
| Five extra prompt rules against padding; reranker instruction rewording | No effect, or mixed | Dropped |
| `granite3.3:8b` | `fix_present` 0.394; never writes the COVERAGE line | Dropped |
| `qwen3:14b` | `fix_present` 0.818, 2.7 to 7.7 s per answer | Dropped |
| Qwen3-Reranker-4B (4-bit) | Ranking mixed, fixes unchanged, rerank 1.4 to 4.9 s | Dropped |
| `rerank_k` 30 to 50 | No gain, slower | Dropped |
| Hybrid search (`EMBEDDING_SETUP=dual`) | Retrieval scores fell (`hit` 1.0 to 0.909) | Left off; the code path works |
| High effort with thinking on | Every answer used the token budget reasoning and came back "not covered" | Thinking off in all presets |
| Thinking at medium effort, 1024 tokens | 6.67 fixes, 8.5 s per answer | Dropped |
| 4 reranked chunks, 4000-character context | Same fixes as 8 / 8000 over 3 sessions each, longer answers | Dropped |
| Short prompt; evidence lines before steps; top-N sentence selection | Lost 1 to 4 fixes each | Dropped; their switches were removed from the code |
| Prompt rule to use what tables say; rule allowing "If …, acknowledge" steps | Each lost a fix in every session. The second also added "acknowledge" steps that the docs do not support | Dropped, never committed |
| Reranker relative cutoff 0.1; reranker input 4096 tokens | Within noise | Left at 0.2 / 2048 |
| Unsupported-step filter at 0.6 | `step_precision` up to about 0.68, but `am.cfg.0001` lost its "restart" step every time (half credit) | Stays at 0.5: fixes come first |
| An extra model call to pick which steps to keep | Lost the fix on two alarms (tested offline) | Not built |

Other findings worth keeping:

- Off-topic sections can reach the generator with high reranker scores. For example,
  `am.fb.0002` gets "Frame Response Error" at 0.96. The 0.6B reranker cannot tell
  them apart, and the tangential steps come from them.
- Loosening the duplicate-step filter is not safe. At a 0.7 threshold it also drops
  distinct actions ("Detach the axis" / "Attach the axis").
- Alarm descriptions are the strongest lever found. A description that names the
  fix's terms steers retrieval to the right section. A narrow description also
  narrows the answer.

## Suggested next steps

In rough order of value for effort:

1. **Grow the gold set.** 20 to 30 more alarms, with `fix_terms.json` entries.
   Everything else is judged against it.
2. **Collect feedback from use.** `/feedback` already stores a rating per answer.
   Next: export rated answers for review, and turn approved ones into gold
   answers. Later, use them as reranker training pairs.
3. **Tables in the context.** Render table rows as sentences ("Error code: specific
   error code from the drive, CoE object 0x1001:00") at chunking time, so the model
   can use them. This targets `am.fb.0002`.
4. **Retrieval for `am.nc.0003`.** Try a section-level boost when a heading matches
   the alarm description, or fine-tune the 0.6B reranker on (alarm, correct section)
   pairs.
5. **A second pass.** Ask the model to check its steps against the context and add
   what it missed. This targets the in-prompt gaps. It costs one more generation
   per answer.
