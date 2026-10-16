# Tuning experiments, 15-16 Oct 2026

A record of tuning experiments, kept for reference. None of these files is read by
the code. Most of the experiments did not change any default.

## How each run was made

Each run is one **session**:

1. Put the run's overrides at the end of `.env`.
2. `make restart`
3. `EVAL_RUNS=3 make eval` (11 gold alarms x 3 passes, `qwen3:8b`, `RESPONSE_CACHE_ENABLED=false`).
4. `python -m eval.diagnose_gaps` (needs `RESOLVE_DEBUG_PROMPT=true`).

Each run name has three files:

- `NAME.json`: the eval summary and the answers for each alarm.
- `NAME_gaps.json`: for each missed gold step, whether it was in the prompt
  (`in_prompt_not_used`) or not (`not_in_prompt`).
- `NAME_timing.txt`: the resolve latency for each request. The first request
  after a restart loads the models, so leave it out.

## Read results across sessions, not within one

The 3 passes inside one session almost always agree. In these runs a restart could
still move the score by a whole fix (0.045), with nothing changed. Most of that came
from `am.fb.0004` flipping between half and full credit. So a setting counted as
better only if it beat every baseline session in at least 2 sessions of its own.

That swing came from the database, not the restart. Every run here used a database
that had been ingested earlier and was not re-ingested. After a clean ingest on 16
Oct (fresh volumes, same settings, `qwen3:8b`, 8 chunks, `STEP_SUPPORT_MIN=0.5`):

- 10 `make eval` runs, including after restarts, all scored `fix_solved` 9 and `fix_present` 0.909;
- `am.fb.0004` was full in every run;
- step_precision was 0.637, against 0.57-0.61 here.

The documents retrieved were the same, so the eval's retrieval scores never showed
the difference. The chunk text in the old index probably differed, for example
chunks left from an earlier chunker version. Comparisons within this folder are
still fair, because each was made on the same database. Their absolute scores
understate a clean install, though. Run `make reingest` before an eval you want to
compare with others.

## Runs

| Prefix | What was tested | Outcome |
|---|---|---|
| `r0_baseline`, `ra_*`, `rb_*`, `rc*_*`, `rd_*`, `re_*` | The prompt/context ladder: 4 chunks with a 4000-character context, the short prompt, evidence first, sentence selection, `qwen3:14b` | Every rung stayed off. Rung A first looked like a gain, then matched the old defaults over 3 sessions each (`old8_*`, `t0_defaults*`, `ra_repeat`) and was reverted |
| `t*_s*`, `v_*_s*` | `RESOLVE_TABLE_RULE=use` and `RESOLVE_INFORMATIONAL_STEPS=true`, on code that has since been removed | Both lost a fix, alone and together. The informational rule also added unsupported "acknowledge" steps. Discarded |
| `e1_*` | `RERANK_RELATIVE_MIN=0.1` | Within the baseline's noise |
| `e2_*` | `RERANK_MAX_LENGTH=4096` | Within the baseline's noise (`b8_*` reached the same 9 fixes) |
| `e12_*` | e1 and e2 together | 8 fixes, no gain |
| `e3_*` | `STEP_SUPPORT_MIN=0.6` | Total fixes looked unchanged, and step_precision rose from 0.57-0.61 to 0.64, but per alarm it costs one: `am.cfg.0001` drops to half in all 4 sessions at 0.6 (`e3_*`, `v_base_*`) and is full in all 5 at 0.5 (`old8_*`, `b8_*`). The filter removes "Restart the system to apply changes", which the eval's fix requires. The total hid the loss because `am.fb.0004` happened to be full in both e3 sessions. Adopted, then dropped: the default stays 0.5, to keep more fixes |
| `e4_*` | Thinking mode at medium effort (1024 tokens) | 6.67 fixes, 8.5 s per answer. Rejected |
| `b8_*`, `old8_*`, `v_base_*` | Baselines (8 chunks; `v_base_*` also has `STEP_SUPPORT_MIN=0.6`) | 7.67-9 fixes |

## The remaining gap for am.fb.0002

`am.fb.0002` misses half its fix because the eval also requires the "manufacturer" step
(`eval/fix_terms.json`), not because the "acknowledge" case is missing.
