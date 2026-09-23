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
LOGIN_JSON=$(curl -s -X POST "$BASE/auth/token" -d 'username=smoketest&password=s3cret-pw!')
echo "$LOGIN_JSON"
TOKEN=$(echo "$LOGIN_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "TOKEN_LEN=${#TOKEN}"

echo "--- RESOLVE ---"
curl -s -o /tmp/resolve.json -w 'HTTP %{http_code}\n' -X POST "$BASE/api/v1/resolve" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"code": "am.fb.0002"}'
cat /tmp/resolve.json
echo

echo "--- CHAT ---"
curl -s -o /tmp/chat.json -w 'HTTP %{http_code}\n' -X POST "$BASE/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"conversation_id": "smoke-1", "message": "What should I check first for a drive emergency alarm?"}'
cat /tmp/chat.json
echo

echo "--- CLEANUP ---"
docker compose exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -c \
  "DELETE FROM users WHERE username = 'smoketest';" >/dev/null
