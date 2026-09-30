#!/bin/bash
# Warm multi-query benchmark against the docker compose stack.
#
# Warms the model once (not counted), then runs a batch of real alarm codes back
# to back with the model kept resident, checking each answer is non-empty and free
# of leaked <think> reasoning, and printing per-query timing plus a min/avg/max
# summary and the retrieve/rerank/generate split from the orchestrator log.
#
# Requires: docker compose up (postgres, redis, ollama, orchestrator) and a
# host-side .venv with the project installed (for seeding/cleaning the test user).
#
# Note: this measures WARM steady-state. The first (warm-up) call is reported
# separately as the cold number, which is what a client sees on the first click.
set -e
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

BASE=http://localhost:8080/api/v2
PG_USER=${POSTGRES_USER:-rag}
PG_DB=${POSTGRES_DB:-rag}

# Real codes drawn from alarms.sample.json, spread across modules (fb/nc/cfg/lic)
# so the sample is not one lucky document. Override by exporting BENCH_CODES.
CODES=(${BENCH_CODES:-am.fb.0002 am.fb.0001 am.nc.0003 am.nc.0004 am.cfg.0001 am.lic.0001})

# ---- helpers ---------------------------------------------------------------

# Extracts the "steps" text from a resolve response file.
extract_steps() {
  python3 - "$1" <<'PY' 2>/dev/null || true
import sys, json
try:
    data = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
steps = data.get("steps") or []
print("\n".join(s for s in steps if isinstance(s, str)))
PY
}

# Prints doc coverage, steps, likely causes and citations from a resolve response
# (or the error envelope for a non-200), indented under the timing row.
show_details() {
  python3 - "$1" <<'PY' 2>/dev/null || true
import sys, json
try:
    data = json.load(open(sys.argv[1]))
except Exception:
    print("      (unparseable response)")
    sys.exit(0)
if "error" in data:
    err = data["error"]
    print(f"      error: {err.get('code')}: {err.get('message')}")
    sys.exit(0)
print(f"      alarm   : {data.get('title')} | {data.get('domain')} | "
      f"{data.get('severity_category')} ({data.get('severity')})")
print(f"      coverage: {data.get('doc_coverage')}  (confidence {data.get('confidence')})")
for i, s in enumerate(data.get("steps") or [], 1):
    print(f"      step {i}: {s}")
for c in data.get("likely_causes") or []:
    print(f"      cause : {c}")
for c in data.get("citations") or []:
    print(f"      cite  : {c.get('source')} #{c.get('chunk_id')}")
PY
}

# ---- seed + login ----------------------------------------------------------

echo "--- SEED USER ---"
docker compose exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -c \
  "DELETE FROM users WHERE username = 'benchtest';" >/dev/null
PYTHONUNBUFFERED=1 POSTGRES_HOST=localhost .venv/bin/python - <<'PY'
import asyncio
from rag_engine.auth.tiers import Tier
from rag_engine.auth.user_repository import PostgresUserRepository
from rag_engine.stores.db import init_db_pool
from rag_engine.auth import passwords

async def main():
    init_db_pool()
    repo = PostgresUserRepository()
    pw_hash = await passwords.hash_password("s3cret-pw!")
    user = await repo.create("benchtest", pw_hash, Tier.technician)
    print("seeded user:", user.username, user.tier)

asyncio.run(main())
PY

echo "--- LOGIN ---"
LOGIN_RAW=$(curl -s -w '\nHTTP %{http_code}' -X POST "$BASE/auth/token" \
  -d 'username=benchtest&password=s3cret-pw!')
HTTP_CODE=$(echo "$LOGIN_RAW" | sed -n 's/^HTTP //p')
BODY=$(echo "$LOGIN_RAW" | sed '/^HTTP /d')
if [ "$HTTP_CODE" != "200" ]; then
  echo "login failed (HTTP $HTTP_CODE): $BODY"
  exit 1
fi
TOKEN=$(echo "$BODY" | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "token acquired (len=${#TOKEN})"

# ---- warm-up (cold number, not counted in the summary) ---------------------

echo
echo "--- WARM-UP (cold start: model load + active reranker; reported, not averaged) ---"
read -r COLD_HTTP COLD < <(curl -s -o /tmp/bench.json -w '%{http_code} %{time_total}\n' \
  -X POST "$BASE/resolve" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"code\": \"${CODES[0]}\"}")
printf 'cold first call: %ss (HTTP %s)\n' "$COLD" "$COLD_HTTP"
if [ "$COLD_HTTP" = "404" ]; then
  show_details /tmp/bench.json
  echo "alarm ${CODES[0]} is not in the catalogue -- run 'make seed-alarms' (or 'make ingest') first"
  exit 1
fi

# ---- timed batch -----------------------------------------------------------

echo
echo "--- WARM BATCH (${#CODES[@]} codes) ---"
TIMES=()
FAILURES=0
for code in "${CODES[@]}"; do
  read -r http total < <(curl -s -o /tmp/bench.json \
    -w '%{http_code} %{time_total}\n' -X POST "$BASE/resolve" \
    -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d "{\"code\": \"$code\"}")

  steps=$(extract_steps /tmp/bench.json)

  # correctness gates: 200, non-empty answer, no leaked reasoning trace
  status="ok"
  if [ "$http" != "200" ]; then
    status="HTTP_$http"
    FAILURES=$((FAILURES + 1))
  elif [ -z "$steps" ]; then
    status="EMPTY"
    FAILURES=$((FAILURES + 1))
  elif echo "$steps" | grep -qiE "</?think>|we (do|don).?t have the actual content"; then
    status="BAD(think/ungrounded)"
    FAILURES=$((FAILURES + 1))
  fi

  TIMES+=("$total")
  printf '  %-12s %8ss   %s\n' "$code" "$total" "$status"
  show_details /tmp/bench.json
done

# ---- summary ---------------------------------------------------------------

echo
echo "--- SUMMARY ---"
printf '%s\n' "${TIMES[@]}" | python3 - "$FAILURES" "${#CODES[@]}" <<'PY'
import sys
times = [float(x) for x in sys.stdin.read().split()]
failures, total_n = int(sys.argv[1]), int(sys.argv[2])
if times:
    avg = sum(times) / len(times)
    print(f"warm queries : {len(times)}")
    print(f"min / avg / max : {min(times):.2f}s / {avg:.2f}s / {max(times):.2f}s")
    under5 = sum(1 for t in times if t < 5.0)
    print(f"under 5s     : {under5}/{len(times)}")
print(f"correctness  : {total_n - failures}/{total_n} passed"
      + ("" if failures == 0 else "  <-- FAILURES PRESENT"))
PY

echo
echo "--- RETRIEVAL + STAGE SPLIT (query -> retrieved -> rerank -> generate -> timing, per code) ---"
# 5 lines per resolve: resolve_query, retrieved, rerank_forward (GPU reranker only),
# generate_stats (prompt vs output tokens and tok/s), resolve_timing
docker compose logs --tail=600 orchestrator 2>/dev/null \
  | grep -E "resolve_query|retrieved count|rerank_forward|generate_stats|resolve_timing" \
  | tail -"$(( ${#CODES[@]} * 5 ))" \
  || echo "  (no resolve lines found in orchestrator log)"

# ---- cleanup ---------------------------------------------------------------

echo
echo "--- CLEANUP ---"
docker compose exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -c \
  "DELETE FROM users WHERE username = 'benchtest';" >/dev/null