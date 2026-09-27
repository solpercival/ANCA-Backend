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
echo "--- WARM-UP (cold start: model load + lazy reranker; reported, not averaged) ---"
COLD=$(curl -s -o /dev/null -w '%{time_total}' -X POST "$BASE/resolve" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"code\": \"${CODES[0]}\"}")
printf 'cold first call: %ss\n' "$COLD"

# ---- timed batch -----------------------------------------------------------

echo
echo "--- WARM BATCH (${#CODES[@]} codes) ---"
TIMES=()
FAILURES=0
for code in "${CODES[@]}"; do
  total=$(curl -s -o /tmp/bench.json \
    -w '%{time_total}' -X POST "$BASE/resolve" \
    -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d "{\"code\": \"$code\"}")

  steps=$(extract_steps /tmp/bench.json)

  # correctness gates: non-empty answer, no leaked reasoning trace
  status="ok"
  if [ -z "$steps" ]; then
    status="EMPTY"
    FAILURES=$((FAILURES + 1))
  elif echo "$steps" | grep -qiE "</?think>|we (do|don).?t have the actual content"; then
    status="BAD(think/ungrounded)"
    FAILURES=$((FAILURES + 1))
  fi

  TIMES+=("$total")
  printf '  %-12s %8ss   %s\n' "$code" "$total" "$status"
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
echo "--- STAGE SPLIT (last few resolve_timing log lines) ---"
docker compose logs --tail=200 orchestrator 2>/dev/null \
  | grep "resolve_timing" | tail -"${#CODES[@]}" || echo "  (no resolve_timing lines found in orchestrator log)"

# ---- cleanup ---------------------------------------------------------------

echo
echo "--- CLEANUP ---"
docker compose exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -c \
  "DELETE FROM users WHERE username = 'benchtest';" >/dev/null