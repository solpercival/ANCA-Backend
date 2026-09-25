#!/bin/bash
# End-to-end smoke test against the docker compose stack: auth -> resolve -> chat.
# Requires: docker compose up (postgres, redis, ollama, orchestrator) and a
# host-side .venv with the project installed (for seeding/cleaning the test user).
set -e
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

BASE=http://localhost:8080
PG_USER=${POSTGRES_USER:-rag}
PG_DB=${POSTGRES_DB:-rag}

# Prints the server-side stage timings from a response file, if the field exists.
# Looks for a top-level "timings" object like {"retrieve":.., "rerank":.., "generate":.., "total":..}
print_stage_timings() {
  python3 - "$1" <<'PY' 2>/dev/null || true
import sys, json
try:
    data = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
t = data.get("timings") or data.get("timing")
if isinstance(t, dict):
    parts = ", ".join(f"{k}={float(v):.2f}s" for k, v in t.items())
    print(f"  server stages: {parts}")
PY
}

echo "--- SEED USER ---"
docker compose exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -c \
  "DELETE FROM users WHERE username = 'smoketest';" >/dev/null
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
    user = await repo.create("smoketest", pw_hash, Tier.technician)
    print("seeded user:", user)

asyncio.run(main())
PY

echo "--- LOGIN ---"
LOGIN_JSON=$(curl -s -w '\nTIME %{time_total}s\n' -X POST "$BASE/auth/token" -d 'username=smoketest&password=s3cret-pw!')
echo "$LOGIN_JSON"
TOKEN=$(echo "$LOGIN_JSON" | sed '/^TIME /d' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "TOKEN_LEN=${#TOKEN}"

echo "--- WARM-UP RESOLVE (not timed: pays model load / lazy reranker cold start) ---"
curl -s -o /dev/null -w 'HTTP %{http_code}  warmup=%{time_total}s\n' -X POST "$BASE/api/v1/resolve" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"code": "am.fb.0002"}'

echo "--- RESOLVE (timed) ---"
curl -s -o /tmp/resolve.json -w 'HTTP %{http_code}  total=%{time_total}s  ttfb=%{time_starttransfer}s\n' \
  -X POST "$BASE/api/v1/resolve" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"code": "am.fb.0002"}'
print_stage_timings /tmp/resolve.json
cat /tmp/resolve.json
echo

echo "--- CHAT (timed) ---"
curl -s -o /tmp/chat.json -w 'HTTP %{http_code}  total=%{time_total}s  ttfb=%{time_starttransfer}s\n' \
  -X POST "$BASE/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"conversation_id": "smoke-1", "message": "What should I check first for a drive emergency alarm?"}'
print_stage_timings /tmp/chat.json
cat /tmp/chat.json
echo

echo "--- CLEANUP ---"
docker compose exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -c \
  "DELETE FROM users WHERE username = 'smoketest';" >/dev/null