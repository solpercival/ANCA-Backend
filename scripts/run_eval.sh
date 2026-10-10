#!/bin/bash
# Seed a persistent eval user, then run the live eval against the running stack.
#
# Unlike bench.sh (which creates and then deletes a throwaway user), this keeps a
# standing account so `run_eval.py` can log in on every run. Safe to run repeatedly:
# it creates the user if missing and resets its password/tier if it already exists.
#
# Requires: the stack up (make up -- it adds the GPU override) and a host-side .venv
# with the project installed.
#
# Usage:
#   bash scripts/run_eval.sh [gold_file]
#
# Override defaults by exporting: EVAL_USERNAME, EVAL_PASSWORD, EVAL_GOLD.
set -e
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

HOST=http://localhost:8080
# the API version is defined once, in src/rag_engine/config.py
API_PREFIX=$(.venv/bin/python -c 'from rag_engine.config import API_PREFIX; print(API_PREFIX)')
BASE="$HOST$API_PREFIX"

EVAL_USERNAME=${EVAL_USERNAME:-evaluser}
EVAL_PASSWORD=${EVAL_PASSWORD:-eval-pw!}
EVAL_GOLD=${1:-${EVAL_GOLD:-docs/docs-proto/starter-kit/alarms/reference-answers.json}}

# ---- preflight: stack up? --------------------------------------------------
# health/ready live under the API router prefix, not the root.
echo "--- CHECK STACK ---"
if ! curl -fsS "$BASE/health" >/dev/null 2>&1; then
  echo "orchestrator not reachable at $BASE/health -- start it first: make up  (plain 'docker compose up' skips the GPU override)"
  exit 1
fi
echo "stack reachable at $BASE"

# ---- gold file present? ----------------------------------------------------
if [ ! -f "$EVAL_GOLD" ]; then
  echo "gold file not found: $EVAL_GOLD"
  echo "pass a path as the first argument or set EVAL_GOLD."
  exit 1
fi

# ---- seed (or refresh) the persistent eval user ----------------------------
echo "--- SEED EVAL USER ($EVAL_USERNAME, technician) ---"
PYTHONUNBUFFERED=1 POSTGRES_HOST=localhost \
EVAL_USERNAME="$EVAL_USERNAME" EVAL_PASSWORD="$EVAL_PASSWORD" \
.venv/bin/python - <<'PY'
import asyncio
import os
from rag_engine.auth.tiers import Tier
from rag_engine.auth.user_repository import PostgresUserRepository
from rag_engine.stores.db import init_db_pool
from rag_engine.auth import passwords

USERNAME = os.environ["EVAL_USERNAME"].strip().lower()
PASSWORD = os.environ["EVAL_PASSWORD"]

async def main():
    init_db_pool()
    repo = PostgresUserRepository()
    pw_hash = await passwords.hash_password(PASSWORD)

    user = await repo.create(USERNAME, pw_hash, Tier.technician)
    if user is not None:
        print("seeded eval user:", user.username, user.tier)
        return

    # Already exists: reset password + tier so this run can log in deterministically.
    existing = await repo.get_by_username(USERNAME)
    await repo.update_password_hash(existing.user_id, pw_hash)
    await repo.update_tier(existing.user_id, Tier.technician)
    print("refreshed existing eval user:", USERNAME, "technician")

asyncio.run(main())
PY

# ---- run the eval ----------------------------------------------------------
echo "--- RUN EVAL (gold: $EVAL_GOLD) ---"
EVAL_USERNAME="$EVAL_USERNAME" \
EVAL_PASSWORD="$EVAL_PASSWORD" \
EVAL_API_URL="$BASE" \
.venv/bin/python -m eval.run_eval --gold "$EVAL_GOLD"