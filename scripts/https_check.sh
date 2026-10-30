#!/bin/bash
# Checks the API behind the HTTPS proxy of docker-compose.https.yml (run by `make https`).
# Requires that stack up and a host-side .venv (to seed and remove a test user).
# Prints PASS / FAIL / SKIP per check and exits non-zero if any check failed.
set -u
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.https.yml"
API_PREFIX=$(.venv/bin/python -c 'from rag_engine.config import API_PREFIX; print(API_PREFIX)')
HTTPS=https://localhost:8443$API_PREFIX
PG_USER=${POSTGRES_USER:-rag}
PG_DB=${POSTGRES_DB:-rag}
USERNAME=httpscheck
PASSWORD='https-check-pw!'
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
failed=0

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; failed=1; }
skip() { echo "SKIP  $1"; }

# trust Caddy's local CA for this script only, rather than using curl -k
for _ in $(seq 1 20); do
  $COMPOSE cp caddy:/data/caddy/pki/authorities/local/root.crt "$TMP/root.crt" >/dev/null 2>&1 && break
  sleep 1
done
if [ ! -s "$TMP/root.crt" ]; then
  echo "FAIL  Caddy's root certificate not found; is the caddy service up?"
  exit 1
fi
CURL=(curl -s --cacert "$TMP/root.crt")
# the orchestrator was just recreated; wait for it behind the proxy (model warm-up excluded)
for _ in $(seq 1 60); do
  [ "$("${CURL[@]}" -o /dev/null -w '%{http_code}' "$HTTPS/health")" = 200 ] && break
  sleep 2
done

# 1. HTTPS works with a valid certificate, and HSTS proves X-Forwarded-Proto is trusted
"${CURL[@]}" -D "$TMP/h1" -o /dev/null "$HTTPS/health"
if grep -q "^HTTP/[0-9.]* 200" "$TMP/h1"; then
  pass "GET $HTTPS/health -> 200 with a certificate the local CA signed"
else
  fail "GET $HTTPS/health did not return 200: $(head -1 "$TMP/h1")"
fi
if grep -qi "^strict-transport-security:" "$TMP/h1"; then
  pass "HSTS header sent over HTTPS (the orchestrator sees the request as https)"
else
  fail "no HSTS header over HTTPS: X-Forwarded-Proto from Caddy is not trusted (FORWARDED_ALLOW_IPS?)"
fi

# 2. plain HTTP on the proxy redirects to HTTPS
curl -s -D "$TMP/h2" -o /dev/null "http://localhost:8081$API_PREFIX/health"
if grep -qi "^location: https://localhost:8443$API_PREFIX/health" "$TMP/h2"; then
  pass "http://localhost:8081 redirects to https://localhost:8443"
else
  fail "no HTTPS redirect from :8081: $(head -1 "$TMP/h2")"
fi

# 3. login sets a Secure, HttpOnly refresh cookie, and refresh works with it over HTTPS
$COMPOSE exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -c \
  "DELETE FROM users WHERE username = '$USERNAME';" >/dev/null
POSTGRES_HOST=localhost USERNAME=$USERNAME PASSWORD=$PASSWORD .venv/bin/python - <<'PY'
import asyncio, os
from rag_engine.auth import passwords
from rag_engine.auth.tiers import Tier
from rag_engine.auth.user_repository import PostgresUserRepository
from rag_engine.stores.db import init_db_pool

async def main():
    init_db_pool()
    pw_hash = await passwords.hash_password(os.environ["PASSWORD"])
    await PostgresUserRepository().create(os.environ["USERNAME"], pw_hash, Tier.technician)

asyncio.run(main())
PY
"${CURL[@]}" -D "$TMP/h3" -c "$TMP/jar" -o /dev/null -X POST "$HTTPS/auth/token" \
  -d "username=$USERNAME&password=$PASSWORD"
cookie=$(grep -i "^set-cookie: refresh_token=" "$TMP/h3")
if [ -z "$cookie" ]; then
  fail "login over HTTPS set no refresh cookie: $(head -1 "$TMP/h3")"
elif echo "$cookie" | grep -qi "secure" && echo "$cookie" | grep -qi "httponly"; then
  pass "login sets the refresh cookie with Secure and HttpOnly"
else
  fail "refresh cookie is missing Secure or HttpOnly: $cookie"
fi
code=$("${CURL[@]}" -b "$TMP/jar" -o /dev/null -w '%{http_code}' -X POST "$HTTPS/auth/refresh")
if [ "$code" = 200 ]; then
  pass "POST /auth/refresh with the cookie over HTTPS -> 200"
else
  fail "POST /auth/refresh over HTTPS -> $code"
fi
$COMPOSE exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -c \
  "DELETE FROM users WHERE username = '$USERNAME';" >/dev/null

# 4. the orchestrator logs the real client, not the proxy
since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"${CURL[@]}" -o /dev/null "$HTTPS/health?ip-check=1"
sleep 1
line=$($COMPOSE logs --since "$since" orchestrator 2>/dev/null | grep "ip-check=1" | tail -1)
if [ -z "$line" ]; then
  skip "client IP: no access-log line for the request (uvicorn access log off?)"
elif echo "$line" | grep -q "172.31.250.10:"; then
  fail "orchestrator sees Caddy (172.31.250.10) as the client: $line"
else
  pass "orchestrator sees the client, not Caddy: $(echo "$line" | grep -oE '[0-9]+(\.[0-9]+){3}:[0-9]+' | head -1)"
fi

# 5. a direct caller cannot pretend to be behind the proxy
direct=$(curl -s -D - -o /dev/null -H "X-Forwarded-Proto: https" "http://localhost:8080$API_PREFIX/health")
if echo "$direct" | grep -qi "^strict-transport-security:"; then
  fail "X-Forwarded-Proto from a direct caller on :8080 is trusted (FORWARDED_ALLOW_IPS too wide)"
else
  pass "X-Forwarded-Proto from a direct caller on :8080 is ignored"
fi

# 6. only the configured host names are accepted
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: evil.example" "http://localhost:8080$API_PREFIX/health")
if [ "$code" = 400 ]; then
  pass "Host: evil.example -> 400 (ALLOWED_HOSTS)"
elif [ "${ALLOWED_HOSTS:-}" = "" ] || echo "${ALLOWED_HOSTS:-}" | grep -q '\*'; then
  skip "Host check: ALLOWED_HOSTS allows any host (the local default); set it to test this"
else
  fail "Host: evil.example -> $code, expected 400 with ALLOWED_HOSTS=$ALLOWED_HOSTS"
fi

exit $failed
